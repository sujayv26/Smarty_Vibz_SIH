from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.delay_ripple_service import DelayRippleService
from app.models.delay_impact import DelayImpact
from app.models.wbs_node import WBSNode
from app.models.progress import ProgressEvent
from app.schemas.delay_impact import DelayImpactResponse, DelayImpactListResponse, DelayImpactSummaryResponse
from typing import List, Optional

router = APIRouter(prefix="/delay-impacts", tags=["Delay Impact"])


@router.get("/event/{event_id}", response_model=DelayImpactListResponse)
async def get_delay_impacts_for_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Get all delay ripple impacts for a specific progress event."""
    service = DelayRippleService(db)
    impacts = service.get_delay_impacts_for_event(event_id)
    
    # Enrich with activity details
    enriched_impacts = []
    for impact in impacts:
        enriched = _enrich_impact(db, impact)
        enriched_impacts.append(enriched)
    
    return DelayImpactListResponse(
        impacts=enriched_impacts,
        total_impacted_activities=len(enriched_impacts),
        max_propagated_delay=max((i.propagated_delay_days for i in enriched_impacts), default=0),
        critical_path_impacts=sum(1 for i in enriched_impacts if i.is_critical_path),
    )


@router.get("/activity/{wbs_node_id}", response_model=DelayImpactListResponse)
async def get_delay_impacts_for_activity(
    wbs_node_id: int,
    project_id: int = Query(..., description="Project ID"),
    db: Session = Depends(get_db)
):
    """Get all delay impacts affecting a specific WBS activity."""
    service = DelayRippleService(db)
    impacts = service.get_delay_impacts_for_activity(project_id, wbs_node_id)
    
    enriched_impacts = []
    for impact in impacts:
        enriched = _enrich_impact(db, impact)
        enriched_impacts.append(enriched)
    
    return DelayImpactListResponse(
        impacts=enriched_impacts,
        total_impacted_activities=len(enriched_impacts),
        max_propagated_delay=max((i.propagated_delay_days for i in enriched_impacts), default=0),
        critical_path_impacts=sum(1 for i in enriched_impacts if i.is_critical_path),
    )


@router.get("/project/{project_id}/critical", response_model=DelayImpactListResponse)
async def get_critical_path_impacts(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get all critical path delay impacts for a project."""
    service = DelayRippleService(db)
    impacts = service.get_critical_path_impacts(project_id)
    
    enriched_impacts = []
    for impact in impacts:
        enriched = _enrich_impact(db, impact)
        enriched_impacts.append(enriched)
    
    return DelayImpactListResponse(
        impacts=enriched_impacts,
        total_impacted_activities=len(enriched_impacts),
        max_propagated_delay=max((i.propagated_delay_days for i in enriched_impacts), default=0),
        critical_path_impacts=len(enriched_impacts),
    )


@router.get("/project/{project_id}/summary", response_model=DelayImpactSummaryResponse)
async def get_delay_impact_summary(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get summary of delay impacts for a project."""
    # Get all impacts for project
    all_impacts = db.query(DelayImpact).filter(
        DelayImpact.project_id == project_id
    ).order_by(DelayImpact.computed_at.desc()).all()
    
    # Get unique source events (delay events)
    source_event_ids = set(i.source_event_id for i in all_impacts)
    
    # Get impacted activities
    impacted_activity_ids = set(i.impacted_wbs_node_id for i in all_impacts)
    
    # Critical path impacts
    critical_impacts = [i for i in all_impacts if i.is_critical_path]
    critical_activity_ids = set(i.impacted_wbs_node_id for i in critical_impacts)
    
    # Recent impacts (last 10)
    recent = all_impacts[:10]
    enriched_recent = [_enrich_impact(db, i) for i in recent]
    
    return DelayImpactSummaryResponse(
        project_id=project_id,
        total_delay_events=len(source_event_ids),
        total_impacted_activities=len(impacted_activity_ids),
        critical_path_activities_at_risk=len(critical_activity_ids),
        max_delay_days=max((i.propagated_delay_days for i in all_impacts), default=0),
        recent_impacts=enriched_recent,
    )


@router.post("/event/{event_id}/recompute", response_model=DelayImpactListResponse)
async def recompute_delay_impacts_for_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Recompute delay impacts for a specific event (useful after schedule changes)."""
    event = db.query(ProgressEvent).filter(ProgressEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Progress event not found")
    
    if event.event_type != "DELAY":
        raise HTTPException(status_code=400, detail="Event is not a DELAY event")
    
    # Find the WBS node
    wbs_node = db.query(WBSNode).filter(
        WBSNode.project_id == event.project_id,
        WBSNode.activity_code == event.activity_reference
    ).first()
    
    if not wbs_node:
        raise HTTPException(status_code=404, detail="WBS node not found for event activity")
    
    # Delete existing impacts for this event
    db.query(DelayImpact).filter(DelayImpact.source_event_id == event_id).delete()
    db.commit()
    
    # Recompute
    delay_days = _extract_delay_days(event, db, wbs_node.id)
    service = DelayRippleService(db)
    impacts = service.compute_delay_ripple(
        project_id=event.project_id,
        source_event_id=event_id,
        source_wbs_node_id=wbs_node.id,
        delay_days=delay_days,
    )
    
    enriched_impacts = [_enrich_impact(db, i) for i in impacts]
    
    return DelayImpactListResponse(
        impacts=enriched_impacts,
        total_impacted_activities=len(enriched_impacts),
        max_propagated_delay=max((i.propagated_delay_days for i in enriched_impacts), default=0),
        critical_path_impacts=sum(1 for i in enriched_impacts if i.is_critical_path),
    )


def _enrich_impact(db: Session, impact: DelayImpact) -> DelayImpactResponse:
    """Enrich impact with activity details."""
    response = DelayImpactResponse.model_validate(impact)
    
    # Source activity
    if impact.source_wbs_node_id:
        source_wbs = db.query(WBSNode).filter(WBSNode.id == impact.source_wbs_node_id).first()
        if source_wbs:
            response.source_activity_code = source_wbs.activity_code
            response.source_activity_name = source_wbs.activity_name
    
    # Impacted activity
    impacted_wbs = db.query(WBSNode).filter(WBSNode.id == impact.impacted_wbs_node_id).first()
    if impacted_wbs:
        response.impacted_activity_code = impacted_wbs.activity_code
        response.impacted_activity_name = impacted_wbs.activity_name
        response.impacted_discipline = impacted_wbs.discipline
        response.impacted_wbs = impacted_wbs.wbs
        response.impacted_planned_start = str(impacted_wbs.planned_start) if impacted_wbs.planned_start else None
        response.impacted_planned_finish = str(impacted_wbs.planned_finish) if impacted_wbs.planned_finish else None
    
    return response


def _extract_delay_days(event: ProgressEvent, db: Session, wbs_node_id: int) -> int:
    """Extract delay days from event or delay_reasons table."""
    from app.models.delay_reason import DelayReason
    delay_reason = db.query(DelayReason).filter(
        DelayReason.wbs_node_id == wbs_node_id,
        DelayReason.project_id == event.project_id
    ).order_by(DelayReason.created_at.desc()).first()
    
    if delay_reason:
        return delay_reason.impact_days
    
    import re
    delay_match = re.search(r'delay(?:ed)?\s*(?:by|of)?\s*(\d+)\s*day', event.raw_text, re.IGNORECASE)
    if delay_match:
        return int(delay_match.group(1))
    
    return 1