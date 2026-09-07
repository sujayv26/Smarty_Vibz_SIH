from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    CONTRACTOR_ADMIN = "CONTRACTOR_ADMIN"
    PROJECT_CONTROLS = "PROJECT_CONTROLS"
    DISCIPLINE_PLANNER = "DISCIPLINE_PLANNER"
    SITE_SUPERVISOR = "SITE_SUPERVISOR"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.SITE_SUPERVISOR)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    discipline = Column(String, nullable=True)
    preferred_language = Column(String, nullable=True, default="en")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organization = relationship("Organization", backref="users")