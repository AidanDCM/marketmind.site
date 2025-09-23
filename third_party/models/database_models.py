# database_models.py
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    total_amount = Column(Float, nullable=False)
    customer = relationship("Customer")


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact_info = Column(String)


class CustomerQuery(Base):
    __tablename__ = "customer_queries"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    query_text = Column(String, nullable=False)
    query_timestamp = Column(String, nullable=False)
    resolved = Column(Integer, default=0)  # 0 = unresolved, 1 = resolved
    escalated = Column(Integer, default=0)  # 0 = not escalated, 1 = escalated
    customer = relationship("Customer")
    order = relationship("Order")


class ChatbotInteraction(Base):
    __tablename__ = "chatbot_interactions"
    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey("customer_queries.id"), nullable=False)
    message = Column(String, nullable=False)
    is_bot = Column(Integer, nullable=False)  # 0 = customer message, 1 = bot message
    timestamp = Column(String, nullable=False)
    query = relationship("CustomerQuery")
