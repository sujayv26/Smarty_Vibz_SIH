import json
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.progress import ProgressEvent
from app.models.schedule import ScheduleActivity
from app.models.wbs_node import WBSNode
from app.models.confidence import (
    ConfidenceResult,
    PlannerReview,
    AuditRecord,
    ConfidenceLevel,
    ReviewStatus,
    DecisionType,
    ActorType,
)
from app.matching.service import run_matching_for_event
from app.matching.schemas import MatchingResult
from app.services.confidence_engine import (
    calculate_confidence_score,
    classify_confidence,
    should_auto_match,
    prepare_review_data,
    ConfidenceBreakdown,
)
from app.services.delay_ripple_service import DelayRippleService


def evaluate_confidence(db: Session, progress_event_id: int) -> dict:
    event = db.query(ProgressEvent).filter(ProgressEvent.id == progress_event_id).first()
    if not event:
        raise ValueError(f"Progress event {progress_event_id} not found")
    
    existing_result = db.query(ConfidenceResult).filter(
        ConfidenceResult.progress_event_id == progress_event_id
    ).first()
    if existing_result:
        raise ValueError(f"Confidence already evaluated for progress event {progress_event_id}")
    
    existing_review = db.query(PlannerReview).filter(
        PlannerReview.progress_event_id == progress_event_id
    ).first()
    if existing_review:
        raise ValueError(f"Review already exists for progress event {progress_event_id}")
    
    matching_result = run_matching_for_event(db, progress_event_id)
    
    confidence_score, breakdown = calculate_confidence_score(event, matching_result)
    confidence_level = classify_confidence(confidence_score)
    
    proposed_activity = None
    proposed_activity_id = None
    if matching_result.top_matches:
        top = matching_result.top_matches[0]
        proposed_activity = top
        proposed_activity_id = top.activity_id
    
    confidence_result = ConfidenceResult(
        progress_event_id=progress_event_id,
        proposed_activity_id=proposed_activity_id,
        confidence_score=confidence_score,
        confidence_level=confidence_level,
        decision=DecisionType.AUTO_MATCH if should_auto_match(confidence_level) else DecisionType.REJECTED,
        score_gap=(
            matching_result.top_matches[0].final_score - matching_result.top_matches[1].final_score
            if len(matching_result.top_matches) >= 2 else None
        ),
        exact_identifier_strength=breakdown.exact_identifier_strength,
        fuzzy_similarity=breakdown.fuzzy_similarity,
        semantic_similarity=breakdown.semantic_similarity,
        discipline_compatibility=breakdown.discipline_compatibility,
        context_compatibility=breakdown.context_compatibility,
        temporal_compatibility=breakdown.temporal_compatibility,
        missing_information_penalty=breakdown.missing_information_penalty,
        candidate_ambiguity_penalty=breakdown.candidate_ambiguity_penalty,
    )
    db.add(confidence_result)
    
    if should_auto_match(confidence_level) and proposed_activity_id:
        event.activity_reference = proposed_activity.activity_code
        db.add(event)
        
        audit = AuditRecord(
            progress_event_id=progress_event_id,
            proposed_activity_id=proposed_activity_id,
            final_activity_id=proposed_activity_id,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            decision=DecisionType.AUTO_MATCH,
            actor_type=ActorType.SYSTEM,
        )
        db.add(audit)
        db.commit()
        db.refresh(confidence_result)
        db.refresh(audit)
        
        return {
            "progress_event_id": progress_event_id,
            "proposed_activity": {
                "activity_id": proposed_activity.activity_id,
                "activity_code": proposed_activity.activity_code,
                "activity_name": proposed_activity.activity_name,
                "discipline": proposed_activity.discipline,
            },
            "confidence_score": confidence_score,
            "confidence_level": confidence_level.value,
            "decision": "AUTO_MATCH",
            "requires_review": False,
            "review_id": None,
            "score_breakdown": {
                "exact_identifier_strength": breakdown.exact_identifier_strength,
                "fuzzy_similarity": breakdown.fuzzy_similarity,
                "semantic_similarity": breakdown.semantic_similarity,
                "discipline_compatibility": breakdown.discipline_compatibility,
                "context_compatibility": breakdown.context_compatibility,
                "temporal_compatibility": breakdown.temporal_compatibility,
                "missing_information_penalty": breakdown.missing_information_penalty,
                "candidate_ambiguity_penalty": breakdown.candidate_ambiguity_penalty,
            },
            "top_candidates": matching_result.top_matches,
        }
    else:
        top_candidates, score_breakdown, matching_reasons = prepare_review_data(matching_result)
        
        review = PlannerReview(
            progress_event_id=progress_event_id,
            proposed_activity_id=proposed_activity_id,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            status=ReviewStatus.PENDING,
            top_candidates_json=json.dumps(top_candidates),
            score_breakdown_json=json.dumps(score_breakdown),
            matching_reasons_json=json.dumps(matching_reasons),
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        db.refresh(confidence_result)
        
        return {
            "progress_event_id": progress_event_id,
            "proposed_activity": {
                "activity_id": proposed_activity.activity_id,
                "activity_code": proposed_activity.activity_code,
                "activity_name": proposed_activity.activity_name,
                "discipline": proposed_activity.discipline,
            } if proposed_activity else None,
            "confidence_score": confidence_score,
            "confidence_level": confidence_level.value,
            "decision": "REVIEW_REQUIRED",
            "requires_review": True,
            "review_id": review.id,
            "score_breakdown": {
                "exact_identifier_strength": breakdown.exact_identifier_strength,
                "fuzzy_similarity": breakdown.fuzzy_similarity,
                "semantic_similarity": breakdown.semantic_similarity,
                "discipline_compatibility": breakdown.discipline_compatibility,
                "context_compatibility": breakdown.context_compatibility,
                "temporal_compatibility": breakdown.temporal_compatibility,
                "missing_information_penalty": breakdown.missing_information_penalty,
                "candidate_ambiguity_penalty": breakdown.candidate_ambiguity_penalty,
            },
            "top_candidates": matching_result.top_matches,
        }


def get_pending_reviews(db: Session) -> list[PlannerReview]:
    return db.query(PlannerReview).join(
        ProgressEvent, PlannerReview.progress_event_id == ProgressEvent.id
    ).filter(
        PlannerReview.status == ReviewStatus.PENDING
    ).order_by(PlannerReview.created_at.desc()).all()


def get_review_by_id(db: Session, review_id: int) -> Optional[PlannerReview]:
    return db.query(PlannerReview).join(
        ProgressEvent, PlannerReview.progress_event_id == ProgressEvent.id
    ).filter(PlannerReview.id == review_id).first()


def _write_actuals_to_schedule_activity(db: Session, activity_id: int, event: ProgressEvent) -> None:
    """Write actual start/finish dates to schedule activity based on event type."""
    activity = db.query(ScheduleActivity).filter(ScheduleActivity.id == activity_id).first()
    if not activity or not event.event_date:
        return
    
    if event.event_type == "START" and not activity.actual_start:
        activity.actual_start = event.event_date
        db.add(activity)
    elif event.event_type == "COMPLETE" and not activity.actual_finish:
        activity.actual_finish = event.event_date
        db.add(activity)


def approve_review(db: Session, review_id: int, reviewer_note: Optional[str] = None) -> PlannerReview:
    review = get_review_by_id(db, review_id)
    if not review:
        raise ValueError(f"Review {review_id} not found")
    
    if review.status != ReviewStatus.PENDING:
        raise ValueError(f"Review {review_id} is not pending (status: {review.status.value})")
    
    review.status = ReviewStatus.APPROVED
    review.final_activity_id = review.proposed_activity_id
    review.reviewer_note = reviewer_note
    review.completed_at = func.now()
    
    event = db.query(ProgressEvent).filter(ProgressEvent.id == review.progress_event_id).first()
    if event and review.proposed_activity_id:
        event.activity_reference = review.proposed_activity.activity_code
        db.add(event)
        _write_actuals_to_schedule_activity(db, review.proposed_activity_id, event)
        
        # Trigger delay ripple computation for DELAY events
        if event.event_type == "DELAY" and event.event_date:
            # Get the WBS node for the delayed activity
            wbs_node = db.query(WBSNode).filter(
                WBSNode.project_id == event.project_id,
                WBSNode.activity_code == review.proposed_activity.activity_code
            ).first()
            
            if wbs_node:
                # Get delay days from event raw_text or delay_reason table
                delay_days = _extract_delay_days(event, db, wbs_node.id)
                if delay_days > 0:
                    ripple_service = DelayRippleService(db)
                    ripple_service.compute_delay_ripple(
                        project_id=event.project_id,
                        source_event_id=event.id,
                        source_wbs_node_id=wbs_node.id,
                        delay_days=delay_days,
                    )
    
    audit = AuditRecord(
        progress_event_id=review.progress_event_id,
        proposed_activity_id=review.proposed_activity_id,
        final_activity_id=review.proposed_activity_id,
        confidence_score=review.confidence_score,
        confidence_level=review.confidence_level,
        decision=DecisionType.APPROVED,
        reviewer_note=reviewer_note,
        actor_type=ActorType.PLANNER,
    )
    db.add(audit)
    
    db.commit()
    db.refresh(review)
    return review


def _extract_delay_days(event: ProgressEvent, db: Session, wbs_node_id: int) -> int:
    """Extract delay days from event or delay_reasons table."""
    # First check if there's a delay_reason entry for this activity
    from app.models.delay_reason import DelayReason
    delay_reason = db.query(DelayReason).filter(
        DelayReason.wbs_node_id == wbs_node_id,
        DelayReason.project_id == event.project_id
    ).order_by(DelayReason.created_at.desc()).first()
    
    if delay_reason:
        return delay_reason.impact_days
    
    # Try to extract from raw_text (e.g., "delayed by 5 days")
    import re
    delay_match = re.search(r'delay(?:ed)?\s*(?:by|of)?\s*(\d+)\s*day', event.raw_text, re.IGNORECASE)
    if delay_match:
        return int(delay_match.group(1))
    
    # Default to 1 day if DELAY event type but no explicit delay amount
    return 1


def correct_review(db: Session, review_id: int, activity_id: int, reviewer_note: Optional[str] = None) -> PlannerReview:
    review = get_review_by_id(db, review_id)
    if not review:
        raise ValueError(f"Review {review_id} not found")
    
    if review.status != ReviewStatus.PENDING:
        raise ValueError(f"Review {review_id} is not pending (status: {review.status.value})")
    
    activity = db.query(ScheduleActivity).filter(ScheduleActivity.id == activity_id).first()
    if not activity:
        raise ValueError(f"Activity {activity_id} not found")
    
    review.status = ReviewStatus.CORRECTED
    review.final_activity_id = activity_id
    review.reviewer_note = reviewer_note
    review.completed_at = func.now()
    
    event = db.query(ProgressEvent).filter(ProgressEvent.id == review.progress_event_id).first()
    if event:
        event.activity_reference = activity.activity_code
        db.add(event)
        _write_actuals_to_schedule_activity(db, activity_id, event)
    
    audit = AuditRecord(
        progress_event_id=review.progress_event_id,
        proposed_activity_id=review.proposed_activity_id,
        final_activity_id=activity_id,
        confidence_score=review.confidence_score,
        confidence_level=review.confidence_level,
        decision=DecisionType.CORRECTED,
        reviewer_note=reviewer_note,
        actor_type=ActorType.PLANNER,
    )
    db.add(audit)
    
    db.commit()
    db.refresh(review)
    return review


def reject_review(db: Session, review_id: int, reviewer_note: Optional[str] = None) -> PlannerReview:
    review = get_review_by_id(db, review_id)
    if not review:
        raise ValueError(f"Review {review_id} not found")
    
    if review.status != ReviewStatus.PENDING:
        raise ValueError(f"Review {review_id} is not pending (status: {review.status.value})")
    
    review.status = ReviewStatus.REJECTED
    review.reviewer_note = reviewer_note
    review.completed_at = func.now()
    
    audit = AuditRecord(
        progress_event_id=review.progress_event_id,
        proposed_activity_id=review.proposed_activity_id,
        final_activity_id=None,
        confidence_score=review.confidence_score,
        confidence_level=review.confidence_level,
        decision=DecisionType.REJECTED,
        reviewer_note=reviewer_note,
        actor_type=ActorType.PLANNER,
    )
    db.add(audit)
    
    db.commit()
    db.refresh(review)
    return review


def create_new_activity(
    db: Session,
    review_id: int,
    activity_code: str,
    activity_name: str,
    discipline: str,
    wbs: Optional[str] = None,
    planned_start: Optional[date] = None,
    planned_finish: Optional[date] = None,
    reviewer_note: Optional[str] = None,
) -> PlannerReview:
    from datetime import date
    from sqlalchemy import func
    
    review = get_review_by_id(db, review_id)
    if not review:
        raise ValueError(f"Review {review_id} not found")
    
    if review.status != ReviewStatus.PENDING:
        raise ValueError(f"Review {review_id} is not pending (status: {review.status.value})")
    
    existing = db.query(ScheduleActivity).filter(
        ScheduleActivity.activity_code == activity_code
    ).first()
    if existing:
        raise ValueError(f"Activity code {activity_code} already exists")
    
    if not wbs:
        wbs = f"MISC.{activity_code}"
    
    if not planned_start:
        planned_start = date.today()
    if not planned_finish:
        planned_finish = date.today()
    
    new_activity = ScheduleActivity(
        activity_code=activity_code,
        activity_name=activity_name,
        discipline=discipline,
        wbs=wbs,
        planned_start=planned_start,
        planned_finish=planned_finish,
        is_unplanned=True,
    )
    db.add(new_activity)
    db.flush()
    
    review.status = ReviewStatus.NEW_ACTIVITY_CREATED
    review.final_activity_id = new_activity.id
    review.new_activity_id = new_activity.id
    review.reviewer_note = reviewer_note
    review.completed_at = func.now()
    
    event = db.query(ProgressEvent).filter(ProgressEvent.id == review.progress_event_id).first()
    if event:
        event.activity_reference = activity_code
        db.add(event)
    
    audit = AuditRecord(
        progress_event_id=review.progress_event_id,
        proposed_activity_id=review.proposed_activity_id,
        final_activity_id=new_activity.id,
        new_activity_id=new_activity.id,
        confidence_score=review.confidence_score,
        confidence_level=review.confidence_level,
        decision=DecisionType.NEW_ACTIVITY_CREATED,
        reviewer_note=reviewer_note,
        actor_type=ActorType.PLANNER,
    )
    db.add(audit)
    
    db.commit()
    db.refresh(review)
    db.refresh(new_activity)
    return review


def get_audit_trail(db: Session, progress_event_id: int) -> list[AuditRecord]:
    return db.query(AuditRecord).filter(
        AuditRecord.progress_event_id == progress_event_id
    ).order_by(AuditRecord.created_at).all()