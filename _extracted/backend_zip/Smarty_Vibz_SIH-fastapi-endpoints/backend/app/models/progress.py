from sqlalchemy import Column, Integer, String, Date, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base

class ProgressEvent(Base):
    __tablename__ = "progress_events"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text, nullable=False)
    activity_reference = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    event_date = Column(Date, nullable=True)
    event_time = Column(String, nullable=True)
    discipline = Column(String, nullable=True)
    location = Column(String, nullable=True)
    equipment_tag = Column(String, nullable=True)
    source_type = Column(String, nullable=False)
    source_file = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())