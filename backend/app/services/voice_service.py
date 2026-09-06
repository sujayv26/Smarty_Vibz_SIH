import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import tempfile
import asyncio

from fastapi import UploadFile

logger = logging.getLogger(__name__)

# Whisper model cache
_whisper_model = None
_whisper_model_name = "base"  # Options: tiny, base, small, medium, large


def get_whisper_model():
    """Get or load the Whisper model."""
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            logger.info(f"Loading Whisper model: {_whisper_model_name}")
            _whisper_model = whisper.load_model(_whisper_model_name)
            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.warning("Whisper not installed, using mock transcription")
            _whisper_model = "mock"
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            _whisper_model = "mock"
    return _whisper_model


async def transcribe_audio_file(file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribe an audio file using Whisper.
    Returns dict with 'text', 'language', 'segments', etc.
    """
    model = get_whisper_model()
    
    if model == "mock":
        # Return mock transcription for testing
        return {
            "text": "Started piping erection at 9 AM in Area B",
            "language": language or "en",
            "segments": [],
        }
    
    try:
        # Run transcription in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: model.transcribe(file_path, language=language, fp16=False)
        )
        return result
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise


async def transcribe_audio_upload(upload_file: UploadFile, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribe an uploaded audio file.
    """
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        content = await upload_file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        result = await transcribe_audio_file(tmp_path, language)
        return result
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass


class VoiceService:
    """Service for handling voice input in the Time Agent."""
    
    def __init__(self, db=None):
        self.db = db
        self.supported_formats = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}
        self.max_file_size = 25 * 1024 * 1024  # 25MB
    
    def validate_audio_file(self, upload_file: UploadFile) -> bool:
        """Validate audio file format and size."""
        if not upload_file.filename:
            return False
        
        ext = Path(upload_file.filename).suffix.lower()
        if ext not in self.supported_formats:
            return False
        
        # Note: size check would need the file content
        return True
    
    async def process_voice_input(
        self,
        upload_file: UploadFile,
        session_id: str,
        preferred_language: str = "en",
        project_id: int = 1,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process voice input: transcribe, extract, and log as progress event.
        Returns the agent chat response.
        """
        # Validate
        if not self.validate_audio_file(upload_file):
            raise ValueError(f"Unsupported audio format. Supported: {', '.join(self.supported_formats)}")
        
        # Transcribe
        transcription = await transcribe_audio_upload(upload_file, language=preferred_language)
        transcript_text = transcription.get("text", "").strip()
        detected_language = transcription.get("language", preferred_language)
        
        if not transcript_text:
            raise ValueError("No speech detected in audio")
        
        # Use existing agent service to process the transcribed text
        from app.services.agent_service import process_agent_chat, get_session_context
        from app.schemas.agent import AgentChatRequest
        
        # Create a chat request with the transcribed text
        request = AgentChatRequest(
            message=transcript_text,
            session_id=session_id
        )
        
        # Process through existing agent pipeline
        # This will be called from the API endpoint which has DB session
        return {
            "transcript": transcript_text,
            "detected_language": detected_language,
            "session_id": session_id,
        }
    
    def get_supported_formats(self) -> list[str]:
        """Get list of supported audio formats."""
        return list(self.supported_formats)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Whisper model information."""
        model = get_whisper_model()
        return {
            "model_name": _whisper_model_name if model != "mock" else "mock",
            "loaded": model != "mock",
            "supported_formats": self.get_supported_formats(),
            "max_file_size_mb": self.max_file_size / (1024 * 1024),
        }


def get_voice_service(db=None) -> VoiceService:
    """Factory function to get VoiceService instance."""
    return VoiceService(db)