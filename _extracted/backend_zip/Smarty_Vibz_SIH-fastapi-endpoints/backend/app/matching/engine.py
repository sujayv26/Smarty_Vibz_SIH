from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.progress import ProgressEvent
from app.models.schedule import ScheduleActivity
from app.matching.matchers.exact import exact_match_score
from app.matching.matchers.fuzzy import fuzzy_match_score
from app.matching.matchers.context import context_match_score
from app.matching.matchers.temporal import temporal_match_score
from app.matching.matchers.semantic import get_semantic_matcher
from app.matching.schemas import MatchedActivity, ComponentScores, MatchingResult


WEIGHTS = {
    "exact": 0.30,
    "semantic": 0.25,
    "fuzzy": 0.20,
    "discipline": 0.10,
    "context": 0.10,
    "temporal": 0.05,
}


def get_candidate_activities(db: Session, event: ProgressEvent) -> List[ScheduleActivity]:
    query = db.query(ScheduleActivity)
    
    if event.discipline:
        query = query.filter(ScheduleActivity.discipline.ilike(f"%{event.discipline}%"))
    
    if event.equipment_tag:
        tag = event.equipment_tag.upper()
        query = query.filter(
            (ScheduleActivity.activity_code.ilike(f"%{tag}%")) |
            (ScheduleActivity.activity_name.ilike(f"%{tag}%"))
        )
    
    candidates = query.all()
    
    if not candidates and event.equipment_tag and not event.discipline:
        tag = event.equipment_tag.upper()
        candidates = db.query(ScheduleActivity).filter(
            (ScheduleActivity.activity_code.ilike(f"%{tag}%")) |
            (ScheduleActivity.activity_name.ilike(f"%{tag}%"))
        ).all()
    
    return candidates


def compute_match_scores(event: ProgressEvent, activity: ScheduleActivity) -> tuple[ComponentScores, List[str]]:
    semantic_matcher = get_semantic_matcher()
    
    exact_score, exact_reasons = exact_match_score(event, activity)
    semantic_score, semantic_reasons = semantic_matcher.match(event, activity)
    fuzzy_score, fuzzy_reasons = fuzzy_match_score(event, activity)
    
    from app.matching.matchers.context import discipline_match_score
    discipline_score, discipline_reasons = discipline_match_score(event, activity)
    
    context_score, context_reasons = context_match_score(event, activity)
    
    temporal_score, temporal_reasons = temporal_match_score(event, activity)
    
    all_reasons = []
    all_reasons.extend(exact_reasons)
    all_reasons.extend(semantic_reasons)
    all_reasons.extend(fuzzy_reasons)
    all_reasons.extend(discipline_reasons)
    all_reasons.extend(context_reasons)
    all_reasons.extend(temporal_reasons)
    
    component_scores = ComponentScores(
        exact=exact_score,
        semantic=semantic_score,
        fuzzy=fuzzy_score,
        discipline=discipline_score,
        context=context_score,
        temporal=temporal_score,
    )
    
    return component_scores, all_reasons


def calculate_final_score(component_scores: ComponentScores) -> float:
    return (
        WEIGHTS["exact"] * component_scores.exact +
        WEIGHTS["semantic"] * component_scores.semantic +
        WEIGHTS["fuzzy"] * component_scores.fuzzy +
        WEIGHTS["discipline"] * component_scores.discipline +
        WEIGHTS["context"] * component_scores.context +
        WEIGHTS["temporal"] * component_scores.temporal
    )


def deduplicate_reasons(reasons: List[str]) -> List[str]:
    seen = set()
    unique = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


MIN_MATCH_THRESHOLD = 0.15

def run_matching(db: Session, progress_event_id: int) -> Optional[MatchingResult]:
    event = db.query(ProgressEvent).filter(ProgressEvent.id == progress_event_id).first()
    if not event:
        return None
    
    candidates = get_candidate_activities(db, event)
    
    if not candidates:
        return MatchingResult(progress_event_id=progress_event_id, top_matches=[])
    
    scored_candidates = []
    
    for activity in candidates:
        component_scores, reasons = compute_match_scores(event, activity)
        final_score = calculate_final_score(component_scores)
        
        if final_score >= MIN_MATCH_THRESHOLD:
            unique_reasons = deduplicate_reasons(reasons)
            matched = MatchedActivity(
                activity_id=activity.id,
                activity_code=activity.activity_code,
                activity_name=activity.activity_name,
                discipline=activity.discipline,
                wbs=activity.wbs,
                planned_start=activity.planned_start,
                planned_finish=activity.planned_finish,
                final_score=round(final_score, 4),
                component_scores=component_scores,
                reasons=unique_reasons,
            )
            scored_candidates.append(matched)
    
    scored_candidates.sort(key=lambda x: x.final_score, reverse=True)
    top_matches = scored_candidates[:3]
    
    return MatchingResult(
        progress_event_id=progress_event_id,
        top_matches=top_matches,
    )