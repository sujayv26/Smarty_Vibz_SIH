from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Date, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ProductivityBenchmark(Base):
    __tablename__ = "productivity_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    discipline = Column(String, nullable=False, index=True)
    activity_type = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    planned_quantity = Column(Float, nullable=True)
    actual_quantity = Column(Float, nullable=True)
    planned_duration_days = Column(Float, nullable=True)
    actual_duration_days = Column(Float, nullable=True)
    productivity_rate = Column(Float, nullable=True)
    sample_size = Column(Integer, nullable=False, default=1)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    organization = relationship("Organization", backref="productivity_benchmarks")
    project = relationship("Project", backref="productivity_benchmarks")

    __table_args__ = (
        Index("ix_productivity_benchmarks_org_disc", "organization_id", "discipline"),
        Index("ix_productivity_benchmarks_project_disc", "project_id", "discipline"),
    )