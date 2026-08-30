from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional, Literal

EventType = Literal["START", "PROGRESS", "COMPLETE", "DELAY", "HOLD"]
SourceType = Literal["FREE_TEXT", "EXCEL", "AGENT_CHAT"]

class ProgressEventBase(BaseModel):
    raw_text: str
    activity_reference: Optional[str] = None
    event_type: EventType
    event_date: Optional[date] = None
    event_time: Optional[str] = None
    discipline: Optional[str] = None
    location: Optional[str] = None
    equipment_tag: Optional[str] = None
    source_type: SourceType
    source_file: Optional[str] = None
    session_id: Optional[str] = None

class ProgressEventCreate(ProgressEventBase):
    @field_validator("event_time")
    @classmethod
    def validate_time_format(cls, v):
        if v is not None:
            import re
            if not re.match(r"^\d{2}:\d{2}$", v):
                raise ValueError("event_time must be in HH:MM format")
        return v

class ProgressEventResponse(ProgressEventBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProgressExtractRequest(BaseModel):
    raw_text: str

    @field_validator("raw_text")
    @classmethod
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("raw_text cannot be empty")
        return v.strip()

class ProgressExtractResponse(BaseModel):
    progress_event: ProgressEventResponse
    extracted_data: dict