from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Enum as SQLEnum, Float, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ImpactType(str, enum.Enum):
    DIRECT = "DIRECT"
    PROPAGATED = "PROPAGATED"
    FLOAT_CONSUMED = "FLOAT_CONSUMED"
    CRITICAL_PATH = "CRITICAL_PATH"


class DelayImpact(Base):
    __tablename__ = "delay_impacts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    source_event_id = Column(Integer, ForeignKey("progress_events.id"), nullable=False, index=True)
    source_wbs_node_id = Column(Integer, ForeignKey("wbs_nodes.id"), nullable=True, index=True)
    impacted_wbs_node_id = Column(Integer, ForeignKey("wbs_nodes.id"), nullable=False, index=True)
    impact_type = Column(SQLEnum(ImpactType), nullable=False)
    relationship_type = Column(String, nullable=True)
    lag_days = Column(Integer, default=0, nullable=False)
    original_delay_days = Column(Integer, nullable=False)
    propagated_delay_days = Column(Integer, nullable=False)
    float_consumed_days = Column(Integer, default=0, nullable=False)
    remaining_float_days = Column(Integer, nullable=True)
    is_critical_path = Column(Boolean, default=False, nullable=False)
    critical_path_exposure = Column(Boolean, default=False, nullable=False)
    path_depth = Column(Integer, default=0, nullable=False)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", backref="delay_impacts")
    source_event = relationship("ProgressEvent", backref="delay_impacts")
    source_wbs_node = relationship("WBSNode", foreign_keys=[source_wbs_node_id], backref="source_impacts")
    impacted_wbs_node = relationship("WBSNode", foreign_keys=[impacted_wbs_node_id], backref="impacted_impacts")

    __table_args__ = (
        Index("ix_delay_impacts_project_event", "project_id", "source_event_id"),
        Index("ix_delay_impacts_project_impacted", "project_id", "impacted_wbs_node_id"),
        Index("ix_delay_impacts_critical", "project_id", "is_critical_path"),
    )