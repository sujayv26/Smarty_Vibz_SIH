from sqlalchemy.orm import Session
from app.matching.engine import run_matching
from app.matching.schemas import MatchingResult
from app.models.progress import ProgressEvent


def run_matching_for_event(db: Session, progress_event_id: int) -> MatchingResult:
    result = run_matching(db, progress_event_id)
    if result is None:
        event = db.query(ProgressEvent).filter(ProgressEvent.id == progress_event_id).first()
        if not event:
            raise ValueError(f"Progress event {progress_event_id} not found")
        return MatchingResult(progress_event_id=progress_event_id, top_matches=[])
    return result


def get_progress_event(db: Session, progress_event_id: int) -> ProgressEvent | None:
    return db.query(ProgressEvent).filter(ProgressEvent.id == progress_event_id).first()