from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ScheduleActivity(Base):
    __tablename__ = "schedule_activities"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    activity_code = Column(String, nullable=False, index=True)
    activity_name = Column(String, nullable=False)
    discipline = Column(String, nullable=False)
    wbs = Column(String, nullable=False)
    planned_start = Column(Date, nullable=False)
    planned_finish = Column(Date, nullable=False)
    actual_start = Column(Date, nullable=True)
    actual_finish = Column(Date, nullable=True)
    is_unplanned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    external_schedule_id = Column(Integer, ForeignKey("external_schedules.id"), nullable=True, index=True)
    external_activity_id = Column(String, nullable=True, index=True)
    source_format = Column(String, nullable=True, default="EXCEL")

    external_schedule = relationship("ExternalSchedule", back_populates="activities")
    organization = relationship("Organization", backref="schedule_activities")
    project = relationship("Project", backref="schedule_activities")

    __table_args__ = (
        Index("ix_schedule_activities_org_proj_code", "organization_id", "project_id", "activity_code", unique=True),
    )