from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ExternalSchedule(Base):
    __tablename__ = "external_schedules"

    id = Column(Integer, primary_key=True, index=True)
    external_schedule_id = Column(String, unique=True, index=True, nullable=False)
    schedule_name = Column(String, nullable=True)
    source_filename = Column(String, nullable=True)
    source_format = Column(String, nullable=False, default="XER")
    imported_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(Text, nullable=True)

    activities = relationship("ScheduleActivity", back_populates="external_schedule", lazy="dynamic")
    relationships = relationship("ScheduleRelationship", back_populates="external_schedule", lazy="dynamic")


class ScheduleRelationship(Base):
    __tablename__ = "schedule_relationships"

    id = Column(Integer, primary_key=True, index=True)
    external_schedule_id = Column(Integer, ForeignKey("external_schedules.id"), nullable=True, index=True)
    predecessor_activity_id = Column(Integer, ForeignKey("schedule_activities.id"), nullable=False, index=True)
    successor_activity_id = Column(Integer, ForeignKey("schedule_activities.id"), nullable=False, index=True)
    relationship_type = Column(String, nullable=False)
    lag = Column(Integer, default=0, nullable=False)
    lag_unit = Column(String, default="days", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    external_schedule = relationship("ExternalSchedule", back_populates="relationships")
    predecessor = relationship("ScheduleActivity", foreign_keys=[predecessor_activity_id])
    successor = relationship("ScheduleActivity", foreign_keys=[successor_activity_id])

    __table_args__ = (
        Index("ix_schedule_relationships_pred_succ_type", "predecessor_activity_id", "successor_activity_id", "relationship_type"),
    )