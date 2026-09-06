import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import UploadFile
from io import BytesIO

from app.services.voice_service import VoiceService, get_whisper_model, transcribe_audio_file, transcribe_audio_upload


class TestVoiceService:
    """Tests for the voice service."""

    def test_validate_audio_file(self):
        service = VoiceService()
        
        # Mock valid file
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.wav"
        assert service.validate_audio_file(mock_file) is True
        
        mock_file.filename = "test.mp3"
        assert service.validate_audio_file(mock_file) is True
        
        mock_file.filename = "test.webm"
        assert service.validate_audio_file(mock_file) is True
        
        # Mock invalid file
        mock_file.filename = "test.txt"
        assert service.validate_audio_file(mock_file) is False
        
        mock_file.filename = "test.pdf"
        assert service.validate_audio_file(mock_file) is False

    def test_get_supported_formats(self):
        service = VoiceService()
        formats = service.get_supported_formats()
        assert ".wav" in formats
        assert ".mp3" in formats
        assert ".webm" in formats
        assert ".mp4" not in formats  # video format not supported

    def test_get_model_info(self):
        service = VoiceService()
        info = service.get_model_info()
        assert "model_name" in info
        assert "loaded" in info
        assert "supported_formats" in info
        assert "max_file_size_mb" in info
        assert info["max_file_size_mb"] == 25


class TestWhisperModel:
    """Tests for Whisper model loading."""

    def test_get_whisper_model_mock(self):
        # Should return mock when whisper not available
        model = get_whisper_model()
        # Either returns a model or "mock"
        assert model is not None


class TestTranscription:
    """Tests for audio transcription."""

    @pytest.mark.asyncio
    async def test_transcribe_audio_file_mock(self):
        """Test transcription with mock model."""
        with patch('app.services.voice_service.get_whisper_model', return_value="mock"):
            result = await transcribe_audio_file("/fake/path.wav", language="en")
            assert "text" in result
            assert "language" in result
            assert isinstance(result["text"], str)

    @pytest.mark.asyncio
    async def test_transcribe_audio_upload_mock(self):
        """Test transcription of uploaded file with mock."""
        # Create a mock upload file
        mock_content = b"fake audio data"
        mock_file = MagicMock(spec=UploadFile)
        mock_file.read = AsyncMock(return_value=mock_content)
        mock_file.filename = "test.wav"
        
        with patch('app.services.voice_service.get_whisper_model', return_value="mock"):
            result = await transcribe_audio_upload(mock_file, language="en")
            assert "text" in result
            assert "language" in result
            mock_file.read.assert_called_once()


class TestVoiceProcessRequest:
    """Tests for voice processing request models."""

    def test_voice_upload_response(self):
        from app.schemas.voice import VoiceUploadResponse
        response = VoiceUploadResponse(
            transcript="Test transcript",
            detected_language="en",
            session_id="test-session"
        )
        assert response.transcript == "Test transcript"
        assert response.detected_language == "en"

    def test_voice_model_info(self):
        from app.schemas.voice import VoiceModelInfo
        info = VoiceModelInfo(
            model_name="base",
            loaded=True,
            supported_formats=[".wav", ".mp3"],
            max_file_size_mb=25.0
        )
        assert info.model_name == "base"
        assert info.loaded is True


class TestVoiceServiceIntegration:
    """Integration tests for voice service."""

    def test_service_creation(self):
        service = VoiceService()
        assert service is not None
        assert service.max_file_size == 25 * 1024 * 1024

    def test_process_voice_input_requires_file(self):
        service = VoiceService()
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"  # Invalid format
        
        assert service.validate_audio_file(mock_file) is False

    @pytest.mark.asyncio
    async def test_process_voice_input_invalid_format(self):
        service = VoiceService()
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        
        # Should raise error for invalid format
        with pytest.raises(ValueError, match="Unsupported audio format"):
            await service.process_voice_input(
                mock_file, "session1", "en", 1
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])