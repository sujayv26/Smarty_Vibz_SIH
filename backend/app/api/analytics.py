from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    DisciplineSummaryResponse,
    DelayPatternsResponse,
    BenchmarksResponse,
    VarianceTrendResponse,
    MatchingQualityResponse,
    ConfidenceDistributionResponse,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/discipline-summary", response_model=DisciplineSummaryResponse)
async def get_discipline_summary(
    project_id: int = Query(..., description="Project ID"),
    weeks: int = Query(12, description="Number of weeks to look back"),
    db: Session = Depends(get_db)
):
    """Get discipline-wise summary: actual vs planned duration, productivity index, delay patterns."""
    service = AnalyticsService(db)
    return service.get_discipline_summary(project_id, weeks)


@router.get("/delay-patterns", response_model=DelayPatternsResponse)
async def get_delay_patterns(
    project_id: int = Query(..., description="Project ID"),
    weeks: int = Query(12, description="Number of weeks to look back"),
    db: Session = Depends(get_db)
):
    """Get recurring delay-cause patterns."""
    service = AnalyticsService(db)
    return service.get_delay_patterns(project_id, weeks)


@router.get("/benchmarks", response_model=BenchmarksResponse)
async def get_benchmarks(
    project_id: int = Query(..., description="Project ID"),
    discipline: str = Query(None, description="Filter by discipline"),
    db: Session = Depends(get_db)
):
    """Get productivity benchmarks from historical data."""
    service = AnalyticsService(db)
    return service.get_benchmarks(project_id, discipline)


@router.get("/variance-trend", response_model=VarianceTrendResponse)
async def get_variance_trend(
    project_id: int = Query(..., description="Project ID"),
    weeks: int = Query(12, description="Number of weeks to look back"),
    db: Session = Depends(get_db)
):
    """Get variance trend over time (weekly buckets)."""
    service = AnalyticsService(db)
    return service.get_variance_trend(project_id, weeks)


@router.get("/matching-quality", response_model=MatchingQualityResponse)
async def get_matching_quality(
    project_id: int = Query(..., description="Project ID"),
    weeks: int = Query(12, description="Number of weeks to look back"),
    db: Session = Depends(get_db)
):
    """Get matching quality metrics from planner reviews."""
    service = AnalyticsService(db)
    return service.get_matching_quality(project_id, weeks)


@router.get("/confidence-distribution", response_model=ConfidenceDistributionResponse)
async def get_confidence_distribution(
    project_id: int = Query(..., description="Project ID"),
    weeks: int = Query(12, description="Number of weeks to look back"),
    db: Session = Depends(get_db)
):
    """Get confidence level distribution."""
    service = AnalyticsService(db)
    return service.get_confidence_distribution(project_id, weeks)