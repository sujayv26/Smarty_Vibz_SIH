import os
import logging
import tempfile
from typing import Optional, Dict, Any, List
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF for PDF processing

logger = logging.getLogger(__name__)

# Try to import pytesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not available, using mock OCR")

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp'}
SUPPORTED_PDF_FORMATS = {'.pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class OCRService:
    """Service for OCR processing of scanned diaries and documents."""
    
    def __init__(self, db=None):
        self.db = db
        self.tesseract_config = '--oem 3 --psm 6'  # Default config
    
    def validate_file(self, filename: str, file_size: int) -> bool:
        """Validate file format and size."""
        if file_size > MAX_FILE_SIZE:
            return False
        
        ext = Path(filename).suffix.lower()
        return ext in SUPPORTED_IMAGE_FORMATS or ext in SUPPORTED_PDF_FORMATS
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return list(SUPPORTED_IMAGE_FORMATS | SUPPORTED_PDF_FORMATS)
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results."""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Enhance contrast
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Resize if too small (minimum 1000px width for good OCR)
        if image.width < 1000:
            scale = 1000 / image.width
            new_size = (int(image.width * scale), int(image.height * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image
    
    def extract_text_from_image(self, image: Image.Image, language: str = 'eng') -> Dict[str, Any]:
        """Extract text from a single image using Tesseract."""
        if not TESSERACT_AVAILABLE:
            return {
                "text": "Mock OCR: This is extracted text from a scanned diary page.",
                "language": language,
                "confidence": 0.85,
                "words": [],
            }
        
        try:
            # Preprocess image
            processed = self.preprocess_image(image)
            
            # Extract text with confidence data
            data = pytesseract.image_to_data(
                processed,
                lang=language,
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Combine text
            text_parts = []
            confidences = []
            words = []
            
            for i, word in enumerate(data['text']):
                if word.strip():
                    text_parts.append(word)
                    conf = float(data['conf'][i])
                    confidences.append(conf)
                    words.append({
                        "text": word,
                        "confidence": conf,
                        "bbox": {
                            "x": data['left'][i],
                            "y": data['top'][i],
                            "width": data['width'][i],
                            "height": data['height'][i],
                        }
                    })
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                "text": full_text,
                "language": language,
                "confidence": avg_confidence / 100.0,  # Normalize to 0-1
                "words": words,
            }
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise
    
    def extract_text_from_pdf(self, pdf_path: str, language: str = 'eng') -> Dict[str, Any]:
        """Extract text from PDF by converting pages to images."""
        if not TESSERACT_AVAILABLE:
            return {
                "text": "Mock OCR: Extracted text from PDF diary.",
                "language": language,
                "confidence": 0.85,
                "pages": 1,
            }
        
        try:
            doc = fitz.open(pdf_path)
            all_text = []
            all_words = []
            total_confidence = 0
            page_count = 0
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Render page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Extract text from page
                result = self.extract_text_from_image(img, language)
                
                if result['text'].strip():
                    all_text.append(f"--- Page {page_num + 1} ---\n{result['text']}")
                    all_words.extend(result.get('words', []))
                    total_confidence += result['confidence']
                    page_count += 1
            
            doc.close()
            
            avg_confidence = total_confidence / page_count if page_count > 0 else 0
            
            return {
                "text": '\n\n'.join(all_text),
                "language": language,
                "confidence": avg_confidence,
                "pages": page_count,
                "words": all_words,
            }
        except Exception as e:
            logger.error(f"PDF OCR failed: {e}")
            raise
    
    async def process_upload(
        self,
        file_path: str,
        filename: str,
        language: str = 'eng',
        session_id: str = "default",
    ) -> Dict[str, Any]:
        """Process uploaded file (image or PDF) through OCR."""
        ext = Path(filename).suffix.lower()
        
        if ext in SUPPORTED_IMAGE_FORMATS:
            image = Image.open(file_path)
            result = self.extract_text_from_image(image, language)
            result['pages'] = 1
        elif ext in SUPPORTED_PDF_FORMATS:
            result = self.extract_text_from_pdf(file_path, language)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        
        # Add metadata
        result['filename'] = filename
        result['session_id'] = session_id
        result['source_type'] = 'PDF_OCR'
        
        return result
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OCR model information."""
        return {
            "engine": "tesseract" if TESSERACT_AVAILABLE else "mock",
            "version": pytesseract.get_tesseract_version() if TESSERACT_AVAILABLE else "N/A",
            "available": TESSERACT_AVAILABLE,
            "supported_formats": self.get_supported_formats(),
            "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024),
        }


def get_ocr_service(db=None) -> OCRService:
    """Factory function to get OCRService instance."""
    return OCRService(db)