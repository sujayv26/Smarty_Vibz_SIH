from sqlalchemy.orm import Session
from app.models.progress import ProgressEvent
from app.schemas.progress import ProgressEventCreate, ProgressEventResponse, ProgressExtractResponse
from app.services.extraction_service import get_extraction_provider

def extract_and_store_progress(db: Session, raw_text: str, source_type: str = "FREE_TEXT", source_file: str = None, session_id: str = None) -> ProgressExtractResponse:
    provider = get_extraction_provider()
    extracted = provider.extract_progress(raw_text)
    
    extracted.source_type = source_type
    extracted.source_file = source_file
    extracted.session_id = session_id
    
    progress_event = ProgressEvent(**extracted.model_dump())
    db.add(progress_event)
    db.commit()
    db.refresh(progress_event)
    
    response_event = ProgressEventResponse.model_validate(progress_event)
    return ProgressExtractResponse(
        progress_event=response_event,
        extracted_data=extracted.model_dump()
    )

def get_all_progress_events(db: Session) -> list[ProgressEvent]:
    return db.query(ProgressEvent).order_by(ProgressEvent.created_at.desc()).all()