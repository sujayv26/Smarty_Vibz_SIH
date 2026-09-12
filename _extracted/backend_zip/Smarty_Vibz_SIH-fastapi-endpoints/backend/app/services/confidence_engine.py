from dataclasses import dataclass
from typing import List, Optional
from app.matching.schemas import MatchingResult, MatchedActivity, ComponentScores
from app.models.confidence import ConfidenceLevel
from app.core.config import settings


@dataclass
class ConfidenceBreakdown:
    exact_identifier_strength: float
    fuzzy_similarity: float
    semantic_similarity: float
    discipline_compatibility: float
    context_compatibility: float
    temporal_compatibility: float
    missing_information_penalty: float
    candidate_ambiguity_penalty: float


HIGH_THRESHOLD = 0.80
MEDIUM_THRESHOLD = 0.50


def get_confidence_thresholds() -> tuple[float, float]:
    return HIGH_THRESHOLD, MEDIUM_THRESHOLD


def set_confidence_thresholds(high: float, medium: float) -> None:
    global HIGH_THRESHOLD, MEDIUM_THRESHOLD
    HIGH_THRESHOLD = high
    MEDIUM_THRESHOLD = medium


def calculate_missing_information_penalty(event, top_match: Optional[MatchedActivity]) -> float:
    penalty = 0.0
    if not event.discipline:
        penalty += 0.15
    if not event.location:
        penalty += 0.10
    if not event.equipment_tag:
        penalty += 0.15
    if not event.event_date:
        penalty += 0.10
    if not event.activity_reference:
        penalty += 0.05
    return min(penalty, 0.5)


def calculate_candidate_ambiguity_penalty(top_matches: List[MatchedActivity]) -> float:
    if len(top_matches) < 2:
        return 0.0
    
    score_gap = top_matches[0].final_score - top_matches[1].final_score
    
    if score_gap < 0.05:
        return 0.30
    elif score_gap < 0.10:
        return 0.20
    elif score_gap < 0.20:
        return 0.10
    return 0.0


def calculate_confidence_score(
    event,
    result: MatchingResult,
) -> tuple[float, ConfidenceBreakdown]:
    if not result.top_matches:
        return 0.0, ConfidenceBreakdown(
            exact_identifier_strength=0.0,
            fuzzy_similarity=0.0,
            semantic_similarity=0.0,
            discipline_compatibility=0.0,
            context_compatibility=0.0,
            temporal_compatibility=0.0,
            missing_information_penalty=1.0,
            candidate_ambiguity_penalty=0.0,
        )
    
    top = result.top_matches[0]
    cs = top.component_scores
    
    exact_strength = cs.exact
    fuzzy_sim = cs.fuzzy
    semantic_sim = cs.semantic
    discipline_compat = cs.discipline
    context_compat = cs.context
    temporal_compat = cs.temporal
    
    missing_penalty = calculate_missing_information_penalty(event, top)
    ambiguity_penalty = calculate_candidate_ambiguity_penalty(result.top_matches)
    
    base_score = (
        0.25 * exact_strength +
        0.20 * fuzzy_sim +
        0.20 * semantic_sim +
        0.10 * discipline_compat +
        0.10 * context_compat +
        0.05 * temporal_compat +
        0.10 * top.final_score
    )
    
    confidence = base_score - missing_penalty - ambiguity_penalty
    confidence = max(0.0, min(1.0, confidence))
    
    breakdown = ConfidenceBreakdown(
        exact_identifier_strength=round(exact_strength, 4),
        fuzzy_similarity=round(fuzzy_sim, 4),
        semantic_similarity=round(semantic_sim, 4),
        discipline_compatibility=round(discipline_compat, 4),
        context_compatibility=round(context_compat, 4),
        temporal_compatibility=round(temporal_compat, 4),
        missing_information_penalty=round(missing_penalty, 4),
        candidate_ambiguity_penalty=round(ambiguity_penalty, 4),
    )
    
    return round(confidence, 4), breakdown


def classify_confidence(confidence_score: float) -> ConfidenceLevel:
    high_thresh, medium_thresh = get_confidence_thresholds()
    if confidence_score >= high_thresh:
        return ConfidenceLevel.HIGH
    elif confidence_score >= medium_thresh:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def should_auto_match(confidence_level: ConfidenceLevel) -> bool:
    return confidence_level == ConfidenceLevel.HIGH


def prepare_review_data(result: MatchingResult) -> tuple[list, dict, list]:
    top_candidates = []
    for match in result.top_matches:
        top_candidates.append({
            "activity_id": match.activity_id,
            "activity_code": match.activity_code,
            "activity_name": match.activity_name,
            "discipline": match.discipline,
            "final_score": match.final_score,
            "component_scores": {
                "exact": match.component_scores.exact,
                "semantic": match.component_scores.semantic,
                "fuzzy": match.component_scores.fuzzy,
                "discipline": match.component_scores.discipline,
                "context": match.component_scores.context,
                "temporal": match.component_scores.temporal,
            },
            "reasons": match.reasons,
        })
    
    if result.top_matches:
        top = result.top_matches[0]
        score_breakdown = {
            "exact": top.component_scores.exact,
            "semantic": top.component_scores.semantic,
            "fuzzy": top.component_scores.fuzzy,
            "discipline": top.component_scores.discipline,
            "context": top.component_scores.context,
            "temporal": top.component_scores.temporal,
        }
        matching_reasons = top.reasons
    else:
        score_breakdown = {
            "exact": 0.0, "semantic": 0.0, "fuzzy": 0.0,
            "discipline": 0.0, "context": 0.0, "temporal": 0.0,
        }
        matching_reasons = []
    
    return top_candidates, score_breakdown, matching_reasons