"""Define SQLAlchemy model relationships to avoid circular imports.

This module should be imported after all models are defined to set up
relationships between them.
"""


def setup_relationships() -> None:
    """Set up all model relationships after models are imported.

    This function configures relationships that couldn't be set up in the model
    definitions due to circular imports or other constraints.
    """
    from sqlalchemy.orm import relationship

    from .category import Category
    from .customer import Customer
    from .customer_support import ChatbotInteraction, CustomerQuery
    from .order import Order, OrderItem
    from .product import Product
    from .user import User

    # Configure the main Customer <-> Address relationship
    # These relationships are now defined in the models with viewonly=True
    # We'll just ensure any additional configuration is applied here
    # Note: We're not redefining any relationships here as they're now properly defined in the models

    # Configure Order relationships if not already set
    if not hasattr(Order, "customer"):
        Order.customer = relationship(
            "Customer",
            back_populates="orders",
            foreign_keys="Order.customer_id",
            primaryjoin="Order.customer_id == Customer.id",
        )

    if not hasattr(Order, "items"):
        Order.items = relationship(
            "OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="dynamic"
        )

    # Configure OrderItem relationships if not already set
    if not hasattr(OrderItem, "order"):
        OrderItem.order = relationship(
            "Order",
            back_populates="items",
            foreign_keys="OrderItem.order_id",
            primaryjoin="OrderItem.order_id == Order.id",
        )

    # Configure order addresses if not already set
    if not hasattr(Order, "billing_address"):
        Order.billing_address = relationship(
            "Address", foreign_keys="Order.billing_address_id", post_update=True
        )

    if not hasattr(Order, "shipping_address"):
        Order.shipping_address = relationship(
            "Address", foreign_keys="Order.shipping_address_id", post_update=True
        )

    # Configure Customer.queries if not already set
    if not hasattr(Customer, "queries"):
        Customer.queries = relationship(
            "CustomerQuery",
            back_populates="customer",
            foreign_keys="CustomerQuery.customer_id",
            primaryjoin="Customer.id == CustomerQuery.customer_id",
            lazy="dynamic",
        )

    # Configure CustomerQuery relationships if not already set
    if not hasattr(CustomerQuery, "customer"):
        CustomerQuery.customer = relationship(
            "Customer",
            back_populates="queries",
            foreign_keys="CustomerQuery.customer_id",
            primaryjoin="CustomerQuery.customer_id == Customer.id",
        )

    if not hasattr(CustomerQuery, "assigned_to"):
        CustomerQuery.assigned_to = relationship(
            "User",
            foreign_keys="CustomerQuery.assigned_to_id",
            primaryjoin="CustomerQuery.assigned_to_id == User.id",
        )

    if not hasattr(CustomerQuery, "resolved_by"):
        CustomerQuery.resolved_by = relationship(
            "User",
            foreign_keys="CustomerQuery.resolved_by_id",
            primaryjoin="CustomerQuery.resolved_by_id == User.id",
        )

    # Configure ChatbotInteraction relationships if not already set
    if not hasattr(CustomerQuery, "interactions"):
        CustomerQuery.interactions = relationship(
            "ChatbotInteraction",
            back_populates="query",
            cascade="all, delete-orphan",
            lazy="dynamic",
        )

    if not hasattr(ChatbotInteraction, "query"):
        ChatbotInteraction.query = relationship(
            "CustomerQuery",
            back_populates="interactions",
            foreign_keys="ChatbotInteraction.query_id",
            primaryjoin="ChatbotInteraction.query_id == CustomerQuery.id",
        )

    # Configure User relationships if not already set
    if not hasattr(User, "assigned_queries"):
        User.assigned_queries = relationship(
            "CustomerQuery",
            foreign_keys="CustomerQuery.assigned_to_id",
            back_populates="assigned_to",
            primaryjoin="User.id == CustomerQuery.assigned_to_id",
            lazy="dynamic",
        )

    if not hasattr(User, "resolved_queries"):
        User.resolved_queries = relationship(
            "CustomerQuery",
            foreign_keys="CustomerQuery.resolved_by_id",
            back_populates="resolved_by",
            primaryjoin="User.id == CustomerQuery.resolved_by_id",
            lazy="dynamic",
        )

    # Configure Product and Category relationships if not already set
    if not hasattr(Product, "category"):
        Product.category = relationship(
            "Category",
            back_populates="products",
            foreign_keys="Product.category_id",
            primaryjoin="Product.category_id == Category.id",
            viewonly=False,
        )

    if not hasattr(Category, "products"):
        Category.products = relationship(
            "Product",
            back_populates="category",
            foreign_keys="Product.category_id",
            primaryjoin="Category.id == Product.category_id",
            cascade="all, delete-orphan",
            lazy="dynamic",
        )

    # Configure self-referential Category relationships if not already set
    if not hasattr(Category, "parent"):
        Category.parent = relationship(
            "Category",
            remote_side="Category.id",
            back_populates="children",
            foreign_keys="Category.parent_id",
            primaryjoin="Category.parent_id == Category.id",
            viewonly=False,
        )

    if not hasattr(Category, "children"):
        Category.children = relationship(
            "Category",
            back_populates="parent",
            foreign_keys="Category.parent_id",
            primaryjoin="Category.id == Category.parent_id",
            cascade="all, delete-orphan",
            lazy="dynamic",
        )
