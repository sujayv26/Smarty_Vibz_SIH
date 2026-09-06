from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.services.voice_service import VoiceService, get_voice_service, transcribe_audio_upload
from app.services.agent_service import process_agent_chat, get_session_context
from app.schemas.voice import VoiceUploadResponse, VoiceProcessResponse, VoiceModelInfo
from app.schemas.agent import AgentChatRequest

router = APIRouter(prefix="/voice", tags=["Voice Agent"])


@router.get("/model-info", response_model=VoiceModelInfo)
async def get_voice_model_info():
    """Get information about the Whisper model."""
    service = get_voice_service()
    return service.get_model_info()


@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported audio formats."""
    service = get_voice_service()
    return {"formats": service.get_supported_formats()}


@router.post("/transcribe", response_model=VoiceUploadResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    session_id: str = Form("default"),
):
    """
    Transcribe an uploaded audio file using Whisper.
    """
    service = get_voice_service()
    
    if not service.validate_audio_file(file):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Supported: {', '.join(service.get_supported_formats())}"
        )
    
    try:
        transcription = await transcribe_audio_upload(file, language=language)
        transcript = transcription.get("text", "").strip()
        detected_language = transcription.get("language", language or "en")
        
        if not transcript:
            raise HTTPException(status_code=400, detail="No speech detected in audio")
        
        return VoiceUploadResponse(
            transcript=transcript,
            detected_language=detected_language,
            session_id=session_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/process", response_model=VoiceProcessResponse)
async def process_voice_input(
    file: UploadFile = File(...),
    session_id: str = Form("default"),
    preferred_language: str = Form("en"),
    project_id: int = Form(1),
    db: Session = Depends(get_db),
):
    """
    Process voice input: transcribe and run through agent pipeline.
    This is the main endpoint for voice-based progress logging.
    """
    service = get_voice_service(db)
    
    if not service.validate_audio_file(file):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Supported: {', '.join(service.get_supported_formats())}"
        )
    
    try:
        # Transcribe the audio
        transcription = await transcribe_audio_upload(file, language=preferred_language)
        transcript = transcription.get("text", "").strip()
        detected_language = transcription.get("language", preferred_language)
        
        if not transcript:
            raise HTTPException(status_code=400, detail="No speech detected in audio")
        
        # Process through agent pipeline
        from app.schemas.agent import AgentChatRequest
        request = AgentChatRequest(
            message=transcript,
            session_id=session_id
        )
        
        agent_response = process_agent_chat(db, request, preferred_language=detected_language)
        
        return VoiceProcessResponse(
            transcript=transcript,
            detected_language=detected_language,
            session_id=session_id,
            agent_response=agent_response.model_dump(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")


@router.get("/session/{session_id}/context")
async def get_voice_session_context(session_id: str):
    """Get the current session context for voice interactions."""
    context = get_session_context(session_id)
    return {"session_id": session_id, "context": context}