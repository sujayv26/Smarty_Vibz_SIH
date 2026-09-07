from sqlalchemy.orm import Session
from app.models.progress import ProgressEvent
from app.schemas.progress import ProgressEventCreate, ProgressEventResponse, ProgressExtractResponse
from app.services.extraction_service import get_extraction_provider
from app.models.project import Project

def extract_and_store_progress(db: Session, raw_text: str, source_type: str = "FREE_TEXT", source_file: str = None, session_id: str = None, organization_id: int = None, project_id: int = None, user_id: int = None) -> ProgressExtractResponse:
    provider = get_extraction_provider()
    extracted = provider.extract_progress(raw_text)
    
    extracted.source_type = source_type
    extracted.source_file = source_file
    extracted.session_id = session_id
    
    # Determine project_id if not provided
    if project_id is None and organization_id is not None:
        project = db.query(Project).filter(Project.organization_id == organization_id).first()
        if project:
            project_id = project.id
    
    progress_event = ProgressEvent(
        **extracted.model_dump(),
        organization_id=organization_id,
        project_id=project_id,
        user_id=user_id
    )
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