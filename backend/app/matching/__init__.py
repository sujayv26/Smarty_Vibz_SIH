from app.matching.engine import run_matching
from app.matching.service import run_matching_for_event
from app.matching.benchmark import run_benchmark, BENCHMARK_CASES
from app.matching.schemas import (
    MatchingResult,
    MatchedActivity,
    ComponentScores,
    MatchCategory,
    BenchmarkReport,
    BenchmarkSummary,
    MatchingRunResponse,
    BenchmarkResponse,
)
from app.matching.matchers.exact import exact_match_score
from app.matching.matchers.fuzzy import fuzzy_match_score
from app.matching.matchers.context import context_match_score
from app.matching.matchers.temporal import temporal_match_score
from app.matching.matchers.semantic import SemanticMatcher, OfflineSemanticMatcher, get_semantic_matcher

__all__ = [
    "run_matching",
    "run_matching_for_event",
    "run_benchmark",
    "BENCHMARK_CASES",
    "MatchingResult",
    "MatchedActivity",
    "ComponentScores",
    "MatchCategory",
    "BenchmarkReport",
    "BenchmarkSummary",
    "MatchingRunResponse",
    "BenchmarkResponse",
    "exact_match_score",
    "fuzzy_match_score",
    "context_match_score",
    "temporal_match_score",
    "SemanticMatcher",
    "OfflineSemanticMatcher",
    "get_semantic_matcher",
]