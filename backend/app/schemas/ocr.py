from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class OCRUploadResponse(BaseModel):
    filename: str
    session_id: str
    source_type: str
    text: str
    language: str
    confidence: float
    pages: int
    words: Optional[List[Dict[str, Any]]] = None


class OCRProcessRequest(BaseModel):
    session_id: str = "default"
    language: str = "eng"
    project_id: int = 1


class OCRProcessResponse(BaseModel):
    filename: str
    session_id: str
    source_type: str
    text: str
    language: str
    confidence: float
    pages: int
    agent_response: Optional[Dict[str, Any]] = None


class OCRModelInfo(BaseModel):
    engine: str
    version: str
    available: bool
    supported_formats: List[str]
    max_file_size_mb: float


class ScannedDiary(BaseModel):
    id: int
    session_id: str
    project_id: int
    filename: str
    original_text: str
    language: str
    confidence: float
    pages: int
    status: str  # processing, completed, review_needed, completed
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DiaryUploadResponse(BaseModel):
    diary_id: int
    filename: str
    status: str
    message: str