from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ProgressEvent(Base):
    __tablename__ = "progress_events"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
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
    ingestion_source_id = Column(Integer, ForeignKey("ingestion_sources.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", backref="progress_events")
    project = relationship("Project", backref="progress_events")
    user = relationship("User", backref="progress_events")
    ingestion_source = relationship("IngestionSource", backref="progress_events")

    __table_args__ = (
        Index("ix_progress_events_org_proj_date", "organization_id", "project_id", "event_date"),
    )