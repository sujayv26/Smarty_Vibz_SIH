from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import tempfile
import os
from pathlib import Path

from app.database import get_db
from app.services.ocr_service import OCRService, get_ocr_service
from app.services.agent_service import process_agent_chat
from app.schemas.ocr import (
    OCRUploadResponse,
    OCRProcessResponse,
    OCRModelInfo,
    OCRProcessRequest,
)

router = APIRouter(prefix="/ocr", tags=["OCR Scanned Diaries"])


@router.get("/model-info", response_model=OCRModelInfo)
async def get_ocr_model_info():
    """Get information about the OCR engine."""
    service = get_ocr_service()
    return service.get_model_info()


@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats."""
    service = get_ocr_service()
    return {"formats": service.get_supported_formats()}


@router.post("/upload", response_model=OCRUploadResponse)
async def upload_and_ocr(
    file: UploadFile = File(...),
    language: str = Form("eng"),
    session_id: str = Form("default"),
    db: Session = Depends(get_db),
):
    """
    Upload and OCR a scanned diary image or PDF.
    Returns extracted text without running through agent pipeline.
    """
    service = get_ocr_service()
    
    if not service.validate_file(file.filename, file.size):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format or size. Supported: {', '.join(service.get_supported_formats())}, max 50MB"
        )
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        result = await service.process_upload(
            tmp_path,
            file.filename,
            language=language,
            session_id=session_id,
        )
        
        return OCRUploadResponse(
            filename=result['filename'],
            session_id=result['session_id'],
            source_type=result['source_type'],
            text=result['text'],
            language=result['language'],
            confidence=result['confidence'],
            pages=result['pages'],
            words=result.get('words'),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass


@router.post("/process", response_model=OCRProcessResponse)
async def process_scanned_diary(
    file: UploadFile = File(...),
    session_id: str = Form("default"),
    language: str = Form("eng"),
    project_id: int = Form(1),
    db: Session = Depends(get_db),
):
    """
    Process scanned diary: OCR + run through agent pipeline.
    This is the main endpoint for diary-based progress logging.
    """
    service = get_ocr_service()
    
    if not service.validate_file(file.filename, file.size):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format or size. Supported: {', '.join(service.get_supported_formats())}, max 50MB"
        )
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # OCR the file
        ocr_result = await service.process_upload(
            tmp_path,
            file.filename,
            language=language,
            session_id=session_id,
        )
        
        # Run through agent pipeline
        from app.schemas.agent import AgentChatRequest
        request = AgentChatRequest(
            message=ocr_result['text'],
            session_id=session_id
        )
        
        agent_response = process_agent_chat(db, request, preferred_language=language)
        
        return OCRProcessResponse(
            filename=ocr_result['filename'],
            session_id=ocr_result['session_id'],
            source_type=ocr_result['source_type'],
            text=ocr_result['text'],
            language=ocr_result['language'],
            confidence=ocr_result['confidence'],
            pages=ocr_result['pages'],
            agent_response=agent_response.model_dump(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diary processing failed: {str(e)}")
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass