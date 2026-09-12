from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.confidence_service import (
    get_pending_reviews,
    get_review_by_id,
    approve_review,
    correct_review,
    reject_review,
    create_new_activity,
)
from app.schemas.confidence import (
    PlannerReviewListResponse,
    PlannerReviewResponse,
    ReviewApproveRequest,
    ReviewCorrectRequest,
    ReviewRejectRequest,
    CreateNewActivityRequest,
)

router = APIRouter(prefix="/reviews", tags=["Planner Reviews"])


@router.get("/pending", response_model=PlannerReviewListResponse)
async def get_pending_reviews_endpoint(db: Session = Depends(get_db)):
    reviews = get_pending_reviews(db)
    return _serialize_reviews(reviews)


@router.get("/{review_id}", response_model=PlannerReviewResponse)
async def get_review_endpoint(review_id: int, db: Session = Depends(get_db)):
    review = get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail=f"Review {review_id} not found")
    return _serialize_review(review)


@router.post("/{review_id}/approve", response_model=PlannerReviewResponse)
async def approve_review_endpoint(
    review_id: int,
    request: ReviewApproveRequest,
    db: Session = Depends(get_db)
):
    try:
        review = approve_review(db, review_id, request.reviewer_note)
        return _serialize_review(review)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approve failed: {str(e)}")


@router.post("/{review_id}/correct", response_model=PlannerReviewResponse)
async def correct_review_endpoint(
    review_id: int,
    request: ReviewCorrectRequest,
    db: Session = Depends(get_db)
):
    try:
        review = correct_review(db, review_id, request.activity_id, request.reviewer_note)
        return _serialize_review(review)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correct failed: {str(e)}")


@router.post("/{review_id}/reject", response_model=PlannerReviewResponse)
async def reject_review_endpoint(
    review_id: int,
    request: ReviewRejectRequest,
    db: Session = Depends(get_db)
):
    try:
        review = reject_review(db, review_id, request.reviewer_note)
        return _serialize_review(review)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reject failed: {str(e)}")


@router.post("/{review_id}/create-new", response_model=PlannerReviewResponse)
async def create_new_activity_endpoint(
    review_id: int,
    request: CreateNewActivityRequest,
    db: Session = Depends(get_db)
):
    try:
        review = create_new_activity(
            db=db,
            review_id=review_id,
            activity_code=request.activity_code,
            activity_name=request.activity_name,
            discipline=request.discipline,
            wbs=request.wbs,
            planned_start=request.planned_start,
            planned_finish=request.planned_finish,
            reviewer_note=request.reviewer_note,
        )
        return _serialize_review(review)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Create new activity failed: {str(e)}")


def _serialize_review(review) -> PlannerReviewResponse:
    import json
    from app.schemas.confidence import ProposedActivity, ReviewCandidate, ConfidenceScoreBreakdown
    from app.matching.schemas import ComponentScores
    
    proposed = None
    if review.proposed_activity_id:
        proposed = ProposedActivity(
            activity_id=review.proposed_activity.id,
            activity_code=review.proposed_activity.activity_code,
            activity_name=review.proposed_activity.activity_name,
            discipline=review.proposed_activity.discipline,
        )
    
    top_candidates = []
    if review.top_candidates_json:
        for c in json.loads(review.top_candidates_json):
            top_candidates.append(ReviewCandidate(
                activity_id=c["activity_id"],
                activity_code=c["activity_code"],
                activity_name=c["activity_name"],
                discipline=c["discipline"],
                final_score=c["final_score"],
                component_scores=ComponentScores(**c["component_scores"]),
                reasons=c["reasons"],
            ))
    
    score_breakdown = None
    if review.score_breakdown_json:
        sb = json.loads(review.score_breakdown_json)
        score_breakdown = ConfidenceScoreBreakdown(
            exact_identifier_strength=sb.get("exact", 0.0),
            fuzzy_similarity=sb.get("fuzzy", 0.0),
            semantic_similarity=sb.get("semantic", 0.0),
            discipline_compatibility=sb.get("discipline", 0.0),
            context_compatibility=sb.get("context", 0.0),
            temporal_compatibility=sb.get("temporal", 0.0),
            missing_information_penalty=0.0,
            candidate_ambiguity_penalty=0.0,
        )
    
    matching_reasons = []
    if review.matching_reasons_json:
        matching_reasons = json.loads(review.matching_reasons_json)
    
    return PlannerReviewResponse(
        review_id=review.id,
        progress_event_id=review.progress_event_id,
        proposed_activity=proposed,
        confidence_score=review.confidence_score,
        confidence_level=review.confidence_level.value,
        status=review.status.value,
        top_candidates=top_candidates,
        score_breakdown=score_breakdown,
        matching_reasons=matching_reasons,
        reviewer_note=review.reviewer_note,
        created_at=review.created_at,
        completed_at=review.completed_at,
    )


def _serialize_reviews(reviews) -> PlannerReviewListResponse:
    return PlannerReviewListResponse(reviews=[_serialize_review(r) for r in reviews])