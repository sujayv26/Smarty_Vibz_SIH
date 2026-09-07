from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum, Index, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class DelayCategory(str, enum.Enum):
    WEATHER = "WEATHER"
    RESOURCE = "RESOURCE"
    MATERIAL = "MATERIAL"
    DESIGN = "DESIGN"
    PERMIT = "PERMIT"
    SUBCONTRACTOR = "SUBCONTRACTOR"
    EXTERNAL = "EXTERNAL"
    OTHER = "OTHER"


class DelayReason(Base):
    __tablename__ = "delay_reasons"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    wbs_node_id = Column(Integer, ForeignKey("wbs_nodes.id"), nullable=True, index=True)
    category = Column(SQLEnum(DelayCategory), nullable=False)
    description = Column(Text, nullable=False)
    impact_days = Column(Integer, nullable=False, default=0)
    is_critical_path = Column(Boolean, default=False, nullable=False)
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", backref="delay_reasons")
    wbs_node = relationship("WBSNode", backref="delay_reasons")
    reporter = relationship("User", backref="delay_reasons")

    __table_args__ = (
        Index("ix_delay_reasons_project_category", "project_id", "category"),
    )