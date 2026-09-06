from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from app.models.progress import ProgressEvent
from app.models.schedule import ScheduleActivity
from app.models.delay_reason import DelayReason, DelayCategory
from app.models.productivity_benchmark import ProductivityBenchmark
from app.models.audit_log import AuditLog, AuditAction
from app.models.wbs_node import WBSNode
from app.models.event_wbs_match import EventWBSMatch, MatchType
from app.models.confidence import PlannerReview, ReviewStatus, ConfidenceLevel


class AnalyticsService:
    """SQL aggregations for institutional memory analytics per PRD §6.6."""

    def __init__(self, db: Session):
        self.db = db

    def get_discipline_summary(
        self,
        project_id: int,
        weeks: int = 12,
    ) -> Dict[str, Any]:
        """
        Get discipline-wise summary: actual vs planned duration, 
        productivity index, delay patterns.
        """
        since = date.today() - timedelta(weeks=weeks)

        # Get all activities for this project
        activities = self.db.query(ScheduleActivity).filter(
            ScheduleActivity.project_id == project_id
        ).all()

        discipline_stats = {}

        for activity in activities:
            disc = activity.discipline
            if disc not in discipline_stats:
                discipline_stats[disc] = {
                    "discipline": disc,
                    "total_activities": 0,
                    "planned_duration_days": 0,
                    "actual_duration_days": 0,
                    "completed_activities": 0,
                    "in_progress_activities": 0,
                    "not_started_activities": 0,
                    "delay_events": 0,
                    "delay_days": 0,
                    "delay_categories": {},
                }

            stats = discipline_stats[disc]
            stats["total_activities"] += 1

            duration = (activity.planned_finish - activity.planned_start).days
            stats["planned_duration_days"] += duration

            if activity.actual_finish and activity.actual_start:
                actual_duration = (activity.actual_finish - activity.actual_start).days
                stats["actual_duration_days"] += actual_duration
                stats["completed_activities"] += 1
            elif activity.actual_start:
                stats["in_progress_activities"] += 1
            else:
                stats["not_started_activities"] += 1

        # Get delay reasons by discipline
        delays = self.db.query(DelayReason).filter(
            DelayReason.project_id == project_id,
            DelayReason.created_at >= since
        ).all()

        for delay in delays:
            if delay.wbs_node:
                disc = delay.wbs_node.discipline
                if disc in discipline_stats:
                    discipline_stats[disc]["delay_events"] += 1
                    discipline_stats[disc]["delay_days"] += delay.impact_days
                    cat = delay.category.value
                    discipline_stats[disc]["delay_categories"][cat] = \
                        discipline_stats[disc]["delay_categories"].get(cat, 0) + 1

        # Compute variance and productivity index
        result = []
        for disc, stats in discipline_stats.items():
            planned = stats["planned_duration_days"]
            actual = stats["actual_duration_days"]
            variance = actual - planned if actual > 0 else None
            variance_pct = (variance / planned * 100) if planned > 0 and variance is not None else None
            productivity_index = (planned / actual * 100) if actual > 0 else None

            result.append({
                "discipline": disc,
                "total_activities": stats["total_activities"],
                "completed_activities": stats["completed_activities"],
                "in_progress_activities": stats["in_progress_activities"],
                "not_started_activities": stats["not_started_activities"],
                "planned_duration_days": planned,
                "actual_duration_days": actual if actual > 0 else None,
                "variance_days": variance,
                "variance_pct": round(variance_pct, 1) if variance_pct else None,
                "productivity_index": round(productivity_index, 1) if productivity_index else None,
                "delay_events": stats["delay_events"],
                "delay_days": stats["delay_days"],
                "delay_categories": stats["delay_categories"],
            })

        return {"disciplines": result, "period_weeks": weeks}

    def get_delay_patterns(
        self,
        project_id: int,
        weeks: int = 12,
    ) -> Dict[str, Any]:
        """Get recurring delay-cause patterns."""
        since = date.today() - timedelta(weeks=weeks)

        delays = self.db.query(DelayReason).filter(
            DelayReason.project_id == project_id,
            DelayReason.created_at >= since
        ).all()

        # By category
        by_category = {}
        for delay in delays:
            cat = delay.category.value
            if cat not in by_category:
                by_category[cat] = {
                    "category": cat,
                    "count": 0,
                    "total_days": 0,
                    "avg_days": 0,
                    "critical_path_count": 0,
                }
            by_category[cat]["count"] += 1
            by_category[cat]["total_days"] += delay.impact_days
            if delay.is_critical_path:
                by_category[cat]["critical_path_count"] += 1

        for cat, stats in by_category.items():
            stats["avg_days"] = round(stats["total_days"] / stats["count"], 1) if stats["count"] > 0 else 0

        # By discipline
        by_discipline = {}
        for delay in delays:
            if delay.wbs_node:
                disc = delay.wbs_node.discipline
                if disc not in by_discipline:
                    by_discipline[disc] = {}
                cat = delay.category.value
                by_discipline[disc][cat] = by_discipline[disc].get(cat, 0) + 1

        # Top delay causes
        top_causes = sorted(
            [{"cause": cat, **stats} for cat, stats in by_category.items()],
            key=lambda x: x["total_days"],
            reverse=True
        )[:10]

        return {
            "by_category": list(by_category.values()),
            "by_discipline": by_discipline,
            "top_causes": top_causes,
            "total_delay_events": len(delays),
            "total_delay_days": sum(d.impact_days for d in delays),
            "period_weeks": weeks,
        }

    def get_productivity_index(
        self,
        project_id: int,
        discipline: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get discipline-wise productivity index from benchmarks."""
        query = self.db.query(ProductivityBenchmark).filter(
            ProductivityBenchmark.project_id == project_id
        )
        if discipline:
            query = query.filter(ProductivityBenchmark.discipline == discipline)

        benchmarks = query.all()

        by_discipline = {}
        for bench in benchmarks:
            disc = bench.discipline
            if disc not in by_discipline:
                by_discipline[disc] = {
                    "discipline": disc,
                    "activity_types": [],
                    "avg_productivity_rate": 0,
                    "total_planned_quantity": 0,
                    "total_actual_quantity": 0,
                    "total_planned_duration": 0,
                    "total_actual_duration": 0,
                    "sample_size": 0,
                }
            
            by_discipline[disc]["activity_types"].append({
                "activity_type": bench.activity_type,
                "unit": bench.unit,
                "planned_quantity": bench.planned_quantity,
                "actual_quantity": bench.actual_quantity,
                "planned_duration_days": bench.planned_duration_days,
                "actual_duration_days": bench.actual_duration_days,
                "productivity_rate": bench.productivity_rate,
                "sample_size": bench.sample_size,
                "period_start": str(bench.period_start) if bench.period_start else None,
                "period_end": str(bench.period_end) if bench.period_end else None,
            })
            
            agg = by_discipline[disc]
            agg["total_planned_quantity"] += bench.planned_quantity or 0
            agg["total_actual_quantity"] += bench.actual_quantity or 0
            agg["total_planned_duration"] += bench.planned_duration_days or 0
            agg["total_actual_duration"] += bench.actual_duration_days or 0
            agg["sample_size"] += bench.sample_size
            if bench.productivity_rate:
                agg["avg_productivity_rate"] += bench.productivity_rate

        # Compute averages
        for disc, agg in by_discipline.items():
            count = len(agg["activity_types"])
            if count > 0:
                agg["avg_productivity_rate"] = round(agg["avg_productivity_rate"] / count, 2)

        return {
            "benchmarks": list(by_discipline.values()),
            "project_id": project_id,
        }

    def get_variance_trend(
        self,
        project_id: int,
        weeks: int = 12,
    ) -> Dict[str, Any]:
        """Get variance trend over time (weekly buckets)."""
        since = date.today() - timedelta(weeks=weeks)

        # Get completed activities with actuals
        activities = self.db.query(ScheduleActivity).filter(
            ScheduleActivity.project_id == project_id,
            ScheduleActivity.actual_finish != None,
            ScheduleActivity.actual_finish >= since
        ).all()

        # Bucket by week
        weekly = {}
        for act in activities:
            if not act.actual_finish or not act.actual_start:
                continue
            week_start = act.actual_finish - timedelta(days=act.actual_finish.weekday())
            week_key = str(week_start)
            
            if week_key not in weekly:
                weekly[week_key] = {
                    "week_start": week_key,
                    "planned_days": 0,
                    "actual_days": 0,
                    "completed_count": 0,
                    "delay_events": 0,
                }
            
            planned = (act.planned_finish - act.planned_start).days
            actual = (act.actual_finish - act.actual_start).days
            
            weekly[week_key]["planned_days"] += planned
            weekly[week_key]["actual_days"] += actual
            weekly[week_key]["completed_count"] += 1

        # Get delay events per week
        delays = self.db.query(DelayReason).filter(
            DelayReason.project_id == project_id,
            DelayReason.created_at >= since
        ).all()

        for delay in delays:
            week_start = delay.created_at.date() - timedelta(days=delay.created_at.weekday())
            week_key = str(week_start)
            if week_key in weekly:
                weekly[week_key]["delay_events"] += 1

        # Sort by week and compute variance
        trend = []
        for week_key in sorted(weekly.keys()):
            w = weekly[week_key]
            variance = w["actual_days"] - w["planned_days"]
            variance_pct = (variance / w["planned_days"] * 100) if w["planned_days"] > 0 else 0
            trend.append({
                "week_start": week_key,
                "planned_days": w["planned_days"],
                "actual_days": w["actual_days"],
                "variance_days": variance,
                "variance_pct": round(variance_pct, 1),
                "completed_count": w["completed_count"],
                "delay_events": w["delay_events"],
            })

        return {"trend": trend, "period_weeks": weeks}

    def get_benchmarks(
        self,
        project_id: int,
        discipline: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get productivity benchmarks (alias for get_productivity_index for API compatibility)."""
        return self.get_productivity_index(project_id, discipline)

    def get_matching_quality(
        self,
        project_id: int,
        weeks: int = 12,
    ) -> Dict[str, Any]:
        """Get matching quality metrics from reviews."""
        since = date.today() - timedelta(weeks=weeks)

        reviews = self.db.query(PlannerReview).join(
            ProgressEvent, PlannerReview.progress_event_id == ProgressEvent.id
        ).filter(
            ProgressEvent.project_id == project_id,
            PlannerReview.created_at >= since
        ).all()

        total = len(reviews)
        if total == 0:
            return {
                "total_reviews": 0,
                "auto_commit_rate": 0,
                "review_rate": 0,
                "correction_rate": 0,
                "rejection_rate": 0,
                "new_activity_rate": 0,
                "avg_confidence": 0,
            }

        statuses = [r.status.value for r in reviews]
        confidences = [r.confidence_score for r in reviews]

        return {
            "total_reviews": total,
            "auto_commit_rate": round(statuses.count("APPROVED") / total * 100, 1),
            "review_rate": round(statuses.count("PENDING") / total * 100, 1),
            "correction_rate": round(statuses.count("CORRECTED") / total * 100, 1),
            "rejection_rate": round(statuses.count("REJECTED") / total * 100, 1),
            "new_activity_rate": round(statuses.count("NEW_ACTIVITY_CREATED") / total * 100, 1),
            "avg_confidence": round(sum(confidences) / len(confidences), 3),
            "period_weeks": weeks,
        }

    def get_confidence_distribution(
        self,
        project_id: int,
        weeks: int = 12,
    ) -> Dict[str, Any]:
        """Get confidence level distribution."""
        since = date.today() - timedelta(weeks=weeks)

        confidences = self.db.query(PlannerReview).join(
            ProgressEvent, PlannerReview.progress_event_id == ProgressEvent.id
        ).filter(
            ProgressEvent.project_id == project_id,
            PlannerReview.created_at >= since
        ).all()

        levels = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for c in confidences:
            levels[c.confidence_level.value] += 1

        total = sum(levels.values())
        return {
            "distribution": {k: round(v / total * 100, 1) if total > 0 else 0 for k, v in levels.items()},
            "counts": levels,
            "total": total,
            "period_weeks": weeks,
        }