"""
Audit trail for configuration and flag changes.

This module provides functionality to track changes to configuration values
and feature flags, logging them to both the database and Google Sheets.
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from ..sheets import SheetsClient
from .loader import get_settings

# Configure logger
logger = logging.getLogger(__name__)

# SQLAlchemy models
Base = declarative_base()


class ConfigAudit(Base):
    """Database model for configuration audit trail."""

    __tablename__ = "config_audit"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    actor = Column(String(255), nullable=False)  # User or system that made the change
    key = Column(String(255), nullable=False)  # Config key that was changed
    old_value = Column(Text)  # Old value (redacted if sensitive)
    new_value = Column(Text)  # New value (redacted if sensitive)
    scope = Column(String(50))  # Environment/scope of the change
    change_type = Column(String(50))  # Type of change (create, update, delete)
    metadata_ = Column("metadata", JSON)  # Additional metadata


class AuditChangeType(str, Enum):
    """Types of configuration changes."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ConfigChange(BaseModel):
    """Represents a single configuration change."""

    key: str = Field(..., description="The configuration key that was changed")
    old_value: Optional[Any] = Field(None, description="The old value (redacted if sensitive)")
    new_value: Optional[Any] = Field(None, description="The new value (redacted if sensitive)")
    change_type: AuditChangeType = Field(..., description="Type of change")


class AuditTrail:
    """Handles auditing of configuration and flag changes."""

    def __init__(self, db_url: Optional[str] = None, sheets_client: Optional[SheetsClient] = None):
        """Initialize the audit trail.

        Args:
            db_url: Database URL. If None, uses the default from settings.
            sheets_client: Google Sheets client. If None, one will be created.
        """
        self.settings = get_settings()
        self.db_url = db_url or self.settings.db.url
        self._engine = None
        self._session_factory = None
        self._sheets_client = sheets_client

        # Initialize database
        self._init_db()

    @property
    def engine(self):
        """Get the SQLAlchemy engine, creating it if necessary."""
        if self._engine is None:
            self._engine = create_engine(self.db_url, pool_pre_ping=True, pool_recycle=3600)
        return self._engine

    @property
    def session_factory(self):
        """Get the SQLAlchemy session factory."""
        if self._session_factory is None:
            self._session_factory = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            )
        return self._session_factory

    @property
    def session(self):
        """Get a new database session."""
        return self.session_factory()

    @property
    def sheets_client(self) -> SheetsClient:
        """Get the Google Sheets client, creating it if necessary."""
        if self._sheets_client is None:
            self._sheets_client = SheetsClient()
        return self._sheets_client

    def _init_db(self) -> None:
        """Initialize the database tables if they don't exist."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Initialized config audit database tables")
        except Exception as e:
            logger.error(f"Failed to initialize config audit database: {e}")
            raise

    def log_change(
        self,
        actor: str,
        key: str,
        old_value: Any,
        new_value: Any,
        change_type: Union[AuditChangeType, str],
        scope: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """Log a configuration change.

        Args:
            actor: Who made the change (username, system, etc.)
            key: The configuration key that was changed
            old_value: The old value (will be redacted if sensitive)
            new_value: The new value (will be redacted if sensitive)
            change_type: Type of change (create, update, delete)
            scope: Optional scope/environment for the change
            metadata: Additional metadata about the change

        Returns:
            The ID of the created audit record, or None if logging failed.
        """
        # Convert enum to string if needed
        if isinstance(change_type, AuditChangeType):
            change_type = change_type.value

        # Get scope from settings if not provided
        if scope is None:
            scope = self.settings.env

        # Redact sensitive values
        old_value_str = self._redact_value(key, old_value)
        new_value_str = self._redact_value(key, new_value)

        try:
            # Log to database
            session = self.session
            try:
                audit = ConfigAudit(
                    actor=actor,
                    key=key,
                    old_value=old_value_str,
                    new_value=new_value_str,
                    scope=scope,
                    change_type=change_type,
                    metadata_=metadata or {},
                )

                session.add(audit)
                session.commit()

                # Log to Google Sheets if configured
                self._log_to_sheets(audit)

                return audit.id

            except Exception as e:
                session.rollback()
                logger.error(f"Failed to log config change to database: {e}")
                # Try to log to sheets even if DB fails
                self._log_to_sheets(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "actor": actor,
                        "key": key,
                        "old_value": old_value_str,
                        "new_value": new_value_str,
                        "scope": scope,
                        "change_type": change_type,
                        "metadata": metadata or {},
                    }
                )
                return None

        except Exception as e:
            logger.error(f"Failed to log config change: {e}")
            return None

    def _log_to_sheets(self, audit_data: Union[ConfigAudit, Dict[str, Any]]) -> bool:
        """Log a configuration change to Google Sheets.

        Args:
            audit_data: Either a ConfigAudit instance or a dictionary of audit data.

        Returns:
            bool: True if logging was successful, False otherwise.
        """
        try:
            # Skip if Google Sheets integration is not configured
            if not self.settings.sheets.ledger_spreadsheet_id:
                return False

            # Prepare headers
            headers = [
                "timestamp",
                "actor",
                "key",
                "old_value",
                "new_value",
                "scope",
                "change_type",
                "metadata",
            ]

            # Convert audit data into row shape
            if isinstance(audit_data, ConfigAudit):
                row = [
                    audit_data.timestamp.isoformat(),
                    audit_data.actor,
                    audit_data.key,
                    str(audit_data.old_value)[:500],  # Truncate long values
                    str(audit_data.new_value)[:500],
                    audit_data.scope or self.settings.env,
                    audit_data.change_type,
                    json.dumps(audit_data.metadata_ or {})[:1000],  # Truncate metadata
                ]
            else:
                # Handle dictionary input
                row = [
                    audit_data.get("timestamp", datetime.utcnow().isoformat()),
                    audit_data.get("actor", "system"),
                    audit_data.get("key", ""),
                    str(audit_data.get("old_value", ""))[:500],
                    str(audit_data.get("new_value", ""))[:500],
                    audit_data.get("scope", self.settings.env),
                    audit_data.get("change_type", "update"),
                    json.dumps(audit_data.get("metadata", {}))[:1000],
                ]

            # Append to the "Config Audit" tab using our Sheets client
            self.sheets_client.append_rows(tab="Config Audit", headers=headers, rows=[row])

            return True

        except Exception as e:
            logger.error(f"Failed to log config change to Google Sheets: {e}")
            return False

    def _redact_value(self, key: str, value: Any) -> str:
        """Redact sensitive values before logging."""
        if value is None:
            return ""

        # Convert to string if not already
        if not isinstance(value, str):
            try:
                value = json.dumps(value)
            except (TypeError, ValueError):
                value = str(value)

        # Check if this is a sensitive key that should be redacted
        sensitive_keywords = [
            "password",
            "secret",
            "token",
            "key",
            "credential",
            "api_key",
            "client_secret",
            "refresh_token",
            "access_token",
        ]

        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keywords):
            return "[REDACTED]"

        return value

    def get_changes(
        self,
        key: Optional[str] = None,
        actor: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Retrieve configuration changes from the audit trail.

        Args:
            key: Filter by configuration key
            actor: Filter by actor
            start_date: Filter changes after this date
            end_date: Filter changes before this date
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            List of audit records as dictionaries
        """
        session = self.session
        try:
            query = session.query(ConfigAudit)

            # Apply filters
            if key:
                query = query.filter(ConfigAudit.key == key)
            if actor:
                query = query.filter(ConfigAudit.actor == actor)
            if start_date:
                query = query.filter(ConfigAudit.timestamp >= start_date)
            if end_date:
                query = query.filter(ConfigAudit.timestamp <= end_date)

            # Order by most recent first
            query = query.order_by(ConfigAudit.timestamp.desc())

            # Apply pagination
            query = query.offset(offset).limit(limit)

            # Convert to list of dicts
            return [
                {
                    "id": record.id,
                    "timestamp": record.timestamp.isoformat(),
                    "actor": record.actor,
                    "key": record.key,
                    "old_value": record.old_value,
                    "new_value": record.new_value,
                    "scope": record.scope,
                    "change_type": record.change_type,
                    "metadata": record.metadata_ or {},
                }
                for record in query.all()
            ]

        except Exception as e:
            logger.error(f"Failed to retrieve config changes: {e}")
            return []
        finally:
            session.close()


# Global instance for convenience
audit_trail = AuditTrail()


def log_config_change(
    actor: str,
    key: str,
    old_value: Any,
    new_value: Any,
    change_type: Union[AuditChangeType, str],
    scope: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """Log a configuration change using the global audit trail."""
    return audit_trail.log_change(
        actor=actor,
        key=key,
        old_value=old_value,
        new_value=new_value,
        change_type=change_type,
        scope=scope,
        metadata=metadata,
    )
