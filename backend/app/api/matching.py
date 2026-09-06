from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.matching.service import run_matching_for_event, get_progress_event
from app.matching.benchmark import run_benchmark
from app.matching.schemas import MatchingRunResponse, BenchmarkResponse
from app.models.progress import ProgressEvent
from app.models.project import Project
from app.core.auth import get_current_user

router = APIRouter(prefix="/matching", tags=["Matching"])


@router.post("/run/{progress_event_id}", response_model=MatchingRunResponse)
async def run_matching_endpoint(progress_event_id: int, db: Session = Depends(get_db)):
    event = get_progress_event(db, progress_event_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"Progress event {progress_event_id} not found")
    
    result = run_matching_for_event(db, progress_event_id)
    return result


@router.post("/benchmark", response_model=BenchmarkResponse)
async def run_benchmark_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Get the first project for the user's organization
    project = db.query(Project).filter(Project.organization_id == current_user.organization_id).first()
    project_id = project.id if project else None
    summary = run_benchmark(db, organization_id=current_user.organization_id, project_id=project_id)
    return BenchmarkResponse(summary=summary)