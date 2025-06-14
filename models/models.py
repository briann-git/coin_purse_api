from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from common.db.config import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(String)
    currency = Column(String)

class BudgetItemType(Base):
    __tablename__ = "budget_item_types"
    id = Column(Integer, primary_key=True)
    name = Column(String)

class BudgetItem(Base):
    __tablename__ = "budget_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String)
    description = Column(String)
    type_id = Column(Integer, ForeignKey("budget_item_types.id"))
    expected_amount = Column(Float)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    recurring = Column(Boolean, default=False)

class MonthlyBudgetItem(Base):
    __tablename__ = "monthly_budget_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    budget_item_id = Column(UUID(as_uuid=True), ForeignKey("budget_items.id"))
    actual_amount = Column(Float)
    notes = Column(Text)
    month = Column(Integer)
    year = Column(Integer)
