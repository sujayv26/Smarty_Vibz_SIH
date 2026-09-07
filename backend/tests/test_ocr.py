import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import UploadFile
from io import BytesIO
from pathlib import Path
import tempfile
import os

from app.services.ocr_service import OCRService, get_ocr_service, TESSERACT_AVAILABLE


class TestOCRService:
    """Tests for the OCR service."""

    def test_validate_file(self):
        service = OCRService()
        
        # Mock valid files
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.png"
        mock_file.size = 1024 * 1024  # 1MB
        assert service.validate_file(mock_file.filename, mock_file.size) is True
        
        mock_file.filename = "test.jpg"
        assert service.validate_file(mock_file.filename, mock_file.size) is True
        
        mock_file.filename = "test.pdf"
        assert service.validate_file(mock_file.filename, mock_file.size) is True
        
        mock_file.filename = "test.tiff"
        assert service.validate_file(mock_file.filename, mock_file.size) is True
        
        # Mock invalid files
        mock_file.filename = "test.txt"
        assert service.validate_file(mock_file.filename, mock_file.size) is False
        
        mock_file.filename = "test.doc"
        assert service.validate_file(mock_file.filename, mock_file.size) is False
        
        # File too large
        mock_file.filename = "test.png"
        mock_file.size = 100 * 1024 * 1024  # 100MB
        assert service.validate_file(mock_file.filename, mock_file.size) is False

    def test_get_supported_formats(self):
        service = OCRService()
        formats = service.get_supported_formats()
        assert ".png" in formats
        assert ".jpg" in formats
        assert ".jpeg" in formats
        assert ".pdf" in formats
        assert ".tiff" in formats
        assert ".bmp" in formats
        assert ".webp" in formats

    def test_get_model_info(self):
        service = OCRService()
        info = service.get_model_info()
        assert "engine" in info
        assert "version" in info
        assert "available" in info
        assert "supported_formats" in info
        assert "max_file_size_mb" in info
        assert info["max_file_size_mb"] == 50

    def test_service_creation(self):
        service = OCRService()
        assert service is not None
        assert service.tesseract_config == '--oem 3 --psm 6'

    @pytest.mark.asyncio
    async def test_process_upload_invalid_format(self):
        service = OCRService()
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.size = 1024
        
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"test")
            tmp_path = tmp.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                await service.process_upload(tmp_path, "test.txt", "eng", "session1")
        finally:
            os.unlink(tmp_path)

    def test_preprocess_image(self):
        service = OCRService()
        
        # Create a test image
        from PIL import Image
        img = Image.new('RGB', (500, 500), color='white')
        
        # Preprocess should convert to grayscale and enhance
        processed = service.preprocess_image(img)
        assert processed.mode == 'L'  # Grayscale
        assert processed.width >= 1000  # Should be upscaled


class TestOCRSchemas:
    """Tests for OCR schemas."""

    def test_ocr_upload_response(self):
        from app.schemas.ocr import OCRUploadResponse
        response = OCRUploadResponse(
            filename="test.pdf",
            session_id="test-session",
            source_type="PDF_OCR",
            text="Extracted text",
            language="eng",
            confidence=0.85,
            pages=2,
        )
        assert response.filename == "test.pdf"
        assert response.pages == 2

    def test_ocr_model_info(self):
        from app.schemas.ocr import OCRModelInfo
        info = OCRModelInfo(
            engine="tesseract",
            version="5.3.0",
            available=True,
            supported_formats=[".png", ".pdf"],
            max_file_size_mb=50.0
        )
        assert info.engine == "tesseract"
        assert info.available is True


class TestOCRIntegration:
    """Integration tests for OCR service."""

    def test_service_factory(self):
        service = get_ocr_service()
        assert isinstance(service, OCRService)

    def test_tesseract_availability(self):
        # Tesseract may or may not be available in test environment
        # Just verify the flag exists
        assert isinstance(TESSERACT_AVAILABLE, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])