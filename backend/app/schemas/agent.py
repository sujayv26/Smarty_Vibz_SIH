from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import date

class AgentChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("message cannot be empty")
        return v.strip()

class UnderstoodProgress(BaseModel):
    activity_reference: Optional[str] = None
    event_type: Optional[Literal["START", "PROGRESS", "COMPLETE", "DELAY", "HOLD"]] = None
    event_date: Optional[date] = None
    event_time: Optional[str] = None
    discipline: Optional[str] = None
    location: Optional[str] = None
    equipment_tag: Optional[str] = None

class MatchedActivity(BaseModel):
    activity_code: str
    activity_name: str
    discipline: str
    confidence: float

class AgentChatResponse(BaseModel):
    understood: UnderstoodProgress
    progress_event_id: int
    matched_activity: Optional[MatchedActivity] = None
    confidence: Optional[float] = None
    reply: str
    follow_up: str