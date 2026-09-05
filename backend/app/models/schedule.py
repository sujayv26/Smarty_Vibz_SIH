from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ScheduleActivity(Base):
    __tablename__ = "schedule_activities"

    id = Column(Integer, primary_key=True, index=True)
    activity_code = Column(String, unique=True, index=True, nullable=False)
    activity_name = Column(String, nullable=False)
    discipline = Column(String, nullable=False)
    wbs = Column(String, nullable=False)
    planned_start = Column(Date, nullable=False)
    planned_finish = Column(Date, nullable=False)
    is_unplanned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    external_schedule_id = Column(Integer, ForeignKey("external_schedules.id"), nullable=True, index=True)
    external_activity_id = Column(String, nullable=True, index=True)
    source_format = Column(String, nullable=True, default="EXCEL")

    external_schedule = relationship("ExternalSchedule", back_populates="activities")