import json
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.progress import ProgressEvent
from app.models.schedule import ScheduleActivity
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
    return db.query(PlannerReview).filter(
        PlannerReview.status == ReviewStatus.PENDING
    ).order_by(PlannerReview.created_at.desc()).all()


def get_review_by_id(db: Session, review_id: int) -> Optional[PlannerReview]:
    return db.query(PlannerReview).filter(PlannerReview.id == review_id).first()


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