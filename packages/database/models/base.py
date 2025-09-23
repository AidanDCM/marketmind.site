"""Base database models and utilities.

This module provides the base SQLAlchemy model class and database session utilities.
"""

from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Tuple, TypeVar, cast

from sqlalchemy import create_engine, inspect
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    scoped_session,
    sessionmaker,
)

# Type variable for model classes
T = TypeVar("T", bound="BaseModel")

# Create a thread-safe session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False)

# Create a scoped session factory for use in web applications
ScopedSession = scoped_session(SessionLocal)


class BaseModel(DeclarativeBase):
    """Base model class that provides common functionality for all models.

    This class provides the following features:
    - Automatic table name generation (converts CamelCase to snake_case)
    - Common columns (id, created_at, updated_at)
    - Helper methods for CRUD operations
    """

    # These will be set by SQLAlchemy
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Subclasses may assign a literal table name string.
    # Using ClassVar avoids method-vs-attribute conflicts in mypy.
    __tablename__: ClassVar[str]

    # No need for duplicate column definitions - using Mapped[] above

    @classmethod
    def create(cls, db: Session, **kwargs: Any) -> "BaseModel":
        """Create a new record and save it to the database.

        Args:
            db: Database session
            **kwargs: Column values for the new record

        Returns:
            The created model instance
        """
        obj = cls(**kwargs)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @classmethod
    def get(cls, db: Session, id: int) -> Optional["BaseModel"]:
        """Get a record by ID.

        Args:
            db: Database session
            id: Primary key of the record to retrieve

        Returns:
            The model instance if found, None otherwise
        """
        result = db.query(cls).filter(cls.id == id).first()
        return cast(Optional[BaseModel], result)

    def update(self, db: Session, **kwargs: Any) -> None:
        """Update the record with the given values.

        Args:
            db: Database session
            **kwargs: Column values to update
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        db.add(self)
        db.commit()
        db.refresh(self)

    def delete(self, db: Session) -> None:
        """Delete the record from the database.

        Args:
            db: Database session
        """
        db.delete(self)
        db.commit()

    @classmethod
    def upsert(
        cls,
        db: Session,
        match_attrs: Dict[str, Any],
        values: Optional[Dict[str, Any]] = None,
        update_attrs: Optional[List[str]] = None,
        commit: bool = True,
    ) -> Tuple["BaseModel", bool]:
        """Insert or update a record based on matching attributes.

        If a record matching the given attributes exists, it will be updated.
        If no matching record exists, a new one will be created.

        Args:
            db: Database session
            match_attrs: Dictionary of attributes to match existing records
            values: Dictionary of values to set on create or update
            update_attrs: List of attribute names to update if record exists
                         If None, all attributes in values will be updated
            commit: Whether to commit the transaction immediately

        Returns:
            A tuple of (model_instance, created) where created is a boolean
            indicating whether a new record was created

        Example:
            # Update if exists with email='test@example.com', otherwise create new
            user, created = User.upsert(
                db,
                match_attrs={'email': 'test@example.com'},
                values={'name': 'Test User', 'active': True},
                update_attrs=['name', 'active']
            )
        """
        if values is None:
            values = {}

        # Try to find existing record
        query = db.query(cls)
        for key, value in match_attrs.items():
            query = query.filter(getattr(cls, key) == value)

        existing = query.first()

        if existing:
            # Update existing record
            if update_attrs is None:
                # Update all provided values
                update_values = values
            else:
                # Only update specified attributes
                update_values = {k: v for k, v in values.items() if k in update_attrs}

            for key, value in update_values.items():
                setattr(existing, key, value)

            if commit:
                db.commit()
                db.refresh(existing)

            return existing, False
        else:
            # Create new record with combined match_attrs and values
            create_values = {**match_attrs, **values}
            new_instance = cls(**create_values)
            db.add(new_instance)

            if commit:
                db.commit()
                db.refresh(new_instance)

            return new_instance, True

    @classmethod
    def bulk_upsert(
        cls,
        db: Session,
        records: List[Dict[str, Any]],
        update_columns: Optional[List[str]] = None,
        index_elements: Optional[List[str]] = None,
        batch_size: int = 1000,
    ) -> int:
        """Perform bulk upsert of multiple records.

        This provides better performance than individual upserts for large datasets.

        Args:
            db: Database session
            records: List of dictionaries containing record data
            update_columns: List of column names to update on conflict
                          If None, all columns will be updated
            index_elements: List of column names that make up the unique constraint
                          If None, the primary key will be used
            batch_size: Number of records to process in each batch

        Returns:
            Number of records processed

        Note:
            For SQLite, this falls back to individual upserts since it doesn't
            support ON CONFLICT with multiple rows.
        """
        if not records:
            return 0

        # Get the table and primary key
        mapper = inspect(cls)
        table = mapper.local_table

        if index_elements is None:
            index_elements = [key.name for key in mapper.primary_key]

        if not index_elements:
            raise ValueError("No index_elements provided and no primary key found")

        # For SQLite, fall back to individual upserts
        if db.bind.dialect.name == "sqlite":
            count = 0
            for record in records:
                match_attrs = {k: v for k, v in record.items() if k in index_elements}
                if match_attrs:  # Only proceed if we have keys to match on
                    cls.upsert(
                        db,
                        match_attrs=match_attrs,
                        values=record,
                        update_attrs=update_columns,
                        commit=False,
                    )
                    count += 1

                    # Commit in batches
                    if count % batch_size == 0:
                        db.commit()

            if count % batch_size != 0:  # Commit any remaining changes
                db.commit()

            return count

        # For PostgreSQL, use ON CONFLICT for better performance
        else:
            # If no update columns specified, update all columns except the index columns
            if update_columns is None:
                update_columns = [
                    col.name for col in table.columns if col.name not in index_elements
                ]

            # Process in batches
            total_processed = 0
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]
                if not batch:
                    continue

                # Build the INSERT ... ON CONFLICT ... DO UPDATE statement
                stmt = pg_insert(table).values(batch)

                # Create update dictionary for ON CONFLICT
                update_dict = {col: getattr(stmt.excluded, col) for col in update_columns}

                # Execute the upsert
                stmt = stmt.on_conflict_do_update(index_elements=index_elements, set_=update_dict)

                db.execute(stmt)
                total_processed += len(batch)

                # Commit after each batch
                db.commit()

            return total_processed

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model instance to a dictionary."""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# Create the declarative base
Base = BaseModel


def get_db() -> Session:
    """Get a database session.

    This function is intended to be used as a FastAPI dependency.
    It yields a database session and ensures it's properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(database_url: str) -> None:
    """Initialize the database connection and create tables.

    Args:
        database_url: The database connection URL
    """
    engine = create_engine(database_url)
    SessionLocal.configure(bind=engine)
    Base.metadata.create_all(bind=engine)
