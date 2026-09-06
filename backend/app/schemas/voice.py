from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


class VoiceUploadResponse(BaseModel):
    transcript: str
    detected_language: str
    session_id: str
    duration_seconds: Optional[float] = None


class VoiceProcessRequest(BaseModel):
    session_id: str
    preferred_language: str = "en"
    project_id: int = 1


class VoiceProcessResponse(BaseModel):
    transcript: str
    detected_language: str
    session_id: str
    agent_response: dict  # Full AgentChatResponse


class VoiceModelInfo(BaseModel):
    model_name: str
    loaded: bool
    supported_formats: list[str]
    max_file_size_mb: float


class AudioRecordingSession(BaseModel):
    id: int
    session_id: str
    project_id: int
    user_id: Optional[int] = None
    audio_file_path: Optional[str] = None
    transcript: Optional[str] = None
    detected_language: Optional[str] = None
    duration_seconds: Optional[float] = None
    status: Literal["recording", "transcribing", "completed", "failed"]
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True