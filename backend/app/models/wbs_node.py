from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Date, Index, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pgvector.sqlalchemy import Vector


class WBSNode(Base):
    __tablename__ = "wbs_nodes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    activity_code = Column(String, nullable=False, index=True)
    activity_name = Column(String, nullable=False)
    discipline = Column(String, nullable=False)
    wbs = Column(String, nullable=False, index=True)
    level = Column(Integer, nullable=False, default=1)
    parent_id = Column(Integer, ForeignKey("wbs_nodes.id"), nullable=True, index=True)
    planned_start = Column(Date, nullable=False)
    planned_finish = Column(Date, nullable=False)
    actual_start = Column(Date, nullable=True)
    actual_finish = Column(Date, nullable=True)
    is_unplanned = Column(Boolean, default=False, nullable=False)
    is_milestone = Column(Boolean, default=False, nullable=False)
    description_vector = Column(Vector(1536), nullable=True)
    external_schedule_id = Column(Integer, ForeignKey("external_schedules.id"), nullable=True, index=True)
    external_activity_id = Column(String, nullable=True, index=True)
    source_format = Column(String, nullable=True, default="EXCEL")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship("Project", backref="wbs_nodes")
    parent = relationship("WBSNode", remote_side=[id], backref="children")
    external_schedule = relationship("ExternalSchedule", backref="wbs_nodes")

    __table_args__ = (
        Index("ix_wbs_nodes_project_code", "project_id", "activity_code", unique=True),
        Index("ix_wbs_nodes_project_wbs", "project_id", "wbs"),
    )