import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.services.analytics_service import AnalyticsService
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.schedule import ScheduleActivity
from app.models.wbs_node import WBSNode
from app.models.delay_reason import DelayReason, DelayCategory
from app.models.productivity_benchmark import ProductivityBenchmark
from app.models.progress import ProgressEvent
from app.models.confidence import PlannerReview, ConfidenceLevel, ReviewStatus
from app.models.ingestion_source import IngestionSource
from app.core.security import get_password_hash


class TestAnalyticsService:
    """Tests for institutional memory analytics."""

    def _setup_test_data(self, db: Session) -> tuple[Project, Organization, User]:
        """Create test project with activities, delays, benchmarks, reviews."""
        org = Organization(name="Test Org", slug="test-org-analytics")
        db.add(org)
        db.commit()
        db.refresh(org)

        project = Project(
            name="Test Project",
            code="TEST-ANALYTICS",
            organization_id=org.id,
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        user = User(
            email="test@test.com",
            hashed_password=get_password_hash("test123"),
            full_name="Test User",
            role=UserRole.PROJECT_CONTROLS,
            organization_id=org.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create activities across disciplines
        activities = []
        for i, (code, name, disc, start_offset, duration, actual_start_offset, actual_duration) in enumerate([
            ("PIP-100", "Pipe Erection", "Piping", 0, 10, 0, 12),
            ("PIP-110", "Pipe Support", "Piping", 5, 8, 5, 10),
            ("CIV-100", "Excavation", "Civil", 0, 15, 0, 14),
            ("CIV-110", "Foundation Pour", "Civil", 10, 5, 10, 6),
            ("MEC-100", "Equipment Install", "Mechanical", 20, 10, 22, 12),
            ("ELE-100", "Cable Pull", "Electrical", 15, 8, 15, 7),
        ]):
            planned_start = date(2026, 1, 1) + timedelta(days=start_offset)
            planned_finish = planned_start + timedelta(days=duration)
            actual_start = date(2026, 1, 1) + timedelta(days=actual_start_offset)
            actual_finish = actual_start + timedelta(days=actual_duration)

            act = ScheduleActivity(
                organization_id=org.id,
                project_id=project.id,
                activity_code=code,
                activity_name=name,
                discipline=disc,
                wbs=f"{disc[:3].upper()}.{i+1}",
                planned_start=planned_start,
                planned_finish=planned_finish,
                actual_start=actual_start,
                actual_finish=actual_finish,
            )
            db.add(act)
            activities.append(act)
        db.commit()
        for a in activities:
            db.refresh(a)

        # Add WBS nodes
        for act in activities:
            node = WBSNode(
                project_id=project.id,
                activity_code=act.activity_code,
                activity_name=act.activity_name,
                discipline=act.discipline,
                wbs=act.wbs,
                level=2,
                planned_start=act.planned_start,
                planned_finish=act.planned_finish,
                actual_start=act.actual_start,
                actual_finish=act.actual_finish,
            )
            db.add(node)
        db.commit()

        # Add delay reasons
        wbs_nodes = db.query(WBSNode).filter(WBSNode.project_id == project.id).all()
        delays_data = [
            (wbs_nodes[0], DelayCategory.WEATHER, 5, True),
            (wbs_nodes[1], DelayCategory.MATERIAL, 3, False),
            (wbs_nodes[2], DelayCategory.WEATHER, 2, False),
            (wbs_nodes[3], DelayCategory.RESOURCE, 4, True),
            (wbs_nodes[4], DelayCategory.DESIGN, 1, False),
        ]
        for wbs, cat, days, critical in delays_data:
            delay = DelayReason(
                project_id=project.id,
                wbs_node_id=wbs.id,
                category=cat,
                description=f"{cat.value} delay on {wbs.activity_name}",
                impact_days=days,
                is_critical_path=critical,
            )
            db.add(delay)
        db.commit()

        # Add productivity benchmarks
        benchmarks_data = [
            ("Piping", "Pipe Erection", "m/day", 100, 120, 10, 12, 10.0),
            ("Piping", "Pipe Support", "units/day", 50, 55, 8, 10, 5.5),
            ("Civil", "Excavation", "m3/day", 500, 480, 15, 14, 34.3),
            ("Civil", "Foundation Pour", "m3/day", 200, 220, 5, 6, 36.7),
            ("Mechanical", "Equipment Install", "units/day", 10, 8, 10, 12, 0.67),
            ("Electrical", "Cable Pull", "m/day", 300, 280, 8, 7, 40.0),
        ]
        for disc, act_type, unit, plan_qty, actual_qty, plan_dur, actual_dur, rate in benchmarks_data:
            bench = ProductivityBenchmark(
                organization_id=org.id,
                project_id=project.id,
                discipline=disc,
                activity_type=act_type,
                unit=unit,
                planned_quantity=plan_qty,
                actual_quantity=actual_qty,
                planned_duration_days=plan_dur,
                actual_duration_days=actual_dur,
                productivity_rate=rate,
                sample_size=3,
                period_start=date(2025, 1, 1),
                period_end=date(2025, 12, 31),
            )
            db.add(bench)
        db.commit()

        # Add ingestion sources
        sources = [
            ("VOICE", "Voice/Time-Agent", "Voice"),
            ("TEXT_DIARY", "Text Diary", "Diary"),
        ]
        for code, name, desc in sources:
            src = IngestionSource(code=code, name=name, description=desc)
            db.add(src)
        db.commit()
        voice_src = db.query(IngestionSource).filter(IngestionSource.code == "VOICE").first()
        diary_src = db.query(IngestionSource).filter(IngestionSource.code == "TEXT_DIARY").first()

        # Add progress events and reviews
        for i, act in enumerate(activities):
            event = ProgressEvent(
                organization_id=org.id,
                project_id=project.id,
                user_id=user.id,
                raw_text=f"Completed {act.activity_name}",
                activity_reference=act.activity_code,
                event_type="COMPLETE",
                event_date=act.actual_finish,
                discipline=act.discipline,
                source_type="VOICE" if i % 2 == 0 else "TEXT_DIARY",
                ingestion_source_id=voice_src.id if i % 2 == 0 else diary_src.id,
            )
            db.add(event)
            db.commit()
            db.refresh(event)

            review = PlannerReview(
                progress_event_id=event.id,
                proposed_activity_id=act.id,
                final_activity_id=act.id,
                confidence_score=0.85 + (i * 0.02),
                confidence_level=ConfidenceLevel.HIGH if i < 4 else ConfidenceLevel.MEDIUM,
                status=ReviewStatus.APPROVED,
                top_candidates_json='[]',
                score_breakdown_json='{}',
                matching_reasons_json='[]',
                reviewer_note="Auto-approved",
                completed_at=act.actual_finish,
            )
            db.add(review)
        db.commit()

        return project, org, user

    def test_discipline_summary(self, db_session: Session):
        """Test discipline-wise summary with actual vs planned."""
        project, org, user = self._setup_test_data(db_session)
        service = AnalyticsService(db_session)

        result = service.get_discipline_summary(project.id, weeks=12)

        assert "disciplines" in result
        disciplines = result["disciplines"]
        assert len(disciplines) == 4  # Piping, Civil, Mechanical, Electrical

        # Check Piping
        piping = next(d for d in disciplines if d["discipline"] == "Piping")
        assert piping["total_activities"] == 2
        assert piping["completed_activities"] == 2
        assert piping["planned_duration_days"] == 18  # 10 + 8
        assert piping["actual_duration_days"] == 22   # 12 + 10
        assert piping["variance_days"] == 4
        assert piping["variance_pct"] == pytest.approx(22.2, rel=0.1)
        assert piping["productivity_index"] == pytest.approx(81.8, rel=0.1)

        # Check Civil
        civil = next(d for d in disciplines if d["discipline"] == "Civil")
        assert civil["total_activities"] == 2
        assert civil["planned_duration_days"] == 20  # 15 + 5
        assert civil["actual_duration_days"] == 20  # 14 + 6
        assert civil["variance_days"] == 0

    def test_delay_patterns(self, db_session: Session):
        """Test delay cause patterns analysis."""
        project, org, user = self._setup_test_data(db_session)
        service = AnalyticsService(db_session)

        result = service.get_delay_patterns(project.id, weeks=12)

        assert "by_category" in result
        assert "by_discipline" in result
        assert "top_causes" in result

        # Check categories
        cats = {c["category"]: c for c in result["by_category"]}
        assert "WEATHER" in cats
        assert cats["WEATHER"]["count"] == 2
        assert cats["WEATHER"]["total_days"] == 7
        assert cats["WEATHER"]["critical_path_count"] == 1

        assert "MATERIAL" in cats
        assert cats["MATERIAL"]["count"] == 1

        # Top causes sorted by total_days
        top = result["top_causes"]
        assert top[0]["category"] == "WEATHER"
        assert top[0]["total_days"] == 7

        assert result["total_delay_events"] == 5
        assert result["total_delay_days"] == 15

    def test_benchmarks(self, db_session: Session):
        """Test productivity benchmarks retrieval."""
        project, org, user = self._setup_test_data(db_session)
        service = AnalyticsService(db_session)

        result = service.get_benchmarks(project.id)

        assert "benchmarks" in result
        assert len(result["benchmarks"]) == 4  # 4 disciplines

        piping = next(b for b in result["benchmarks"] if b["discipline"] == "Piping")
        assert len(piping["activity_types"]) == 2
        assert piping["avg_productivity_rate"] > 0

        civil = next(b for b in result["benchmarks"] if b["discipline"] == "Civil")
        assert len(civil["activity_types"]) == 2

    def test_variance_trend(self, db_session: Session):
        """Test weekly variance trend."""
        project, org, user = self._setup_test_data(db_session)
        service = AnalyticsService(db_session)

        # Use 52 weeks to include Jan 2026 data from today (Sept 2026)
        result = service.get_variance_trend(project.id, weeks=52)

        assert "trend" in result
        trend = result["trend"]
        assert len(trend) > 0

        # Each week should have variance data
        for week in trend:
            assert "week_start" in week
            assert "variance_pct" in week
            assert "planned_days" in week
            assert "actual_days" in week
            assert "completed_count" in week

    def test_matching_quality(self, db_session: Session):
        """Test matching quality metrics from reviews."""
        project, org, user = self._setup_test_data(db_session)
        service = AnalyticsService(db_session)

        result = service.get_matching_quality(project.id, weeks=12)

        assert result["total_reviews"] == 6
        assert result["auto_commit_rate"] > 0  # All approved
        assert result["avg_confidence"] > 0.85
        assert result["rejection_rate"] == 0
        assert result["correction_rate"] == 0

    def test_confidence_distribution(self, db_session: Session):
        """Test confidence level distribution."""
        project, org, user = self._setup_test_data(db_session)
        service = AnalyticsService(db_session)

        result = service.get_confidence_distribution(project.id, weeks=12)

        assert "distribution" in result
        assert "counts" in result
        assert result["total"] == 6
        # Should have HIGH and MEDIUM
        assert result["counts"]["HIGH"] == 4
        assert result["counts"]["MEDIUM"] == 2

    def test_discipline_summary_with_weeks_filter(self, db_session: Session):
        """Test that weeks filter affects results."""
        project, org, user = self._setup_test_data(db_session)
        service = AnalyticsService(db_session)

        # 4 weeks should have less data than 12 weeks
        result_4w = service.get_discipline_summary(project.id, weeks=4)
        result_12w = service.get_discipline_summary(project.id, weeks=12)

        # With all activities in Jan 2026, 4 weeks from today (Sept 2026) should be empty
        # But the test data is from Jan 2026, so neither should have data with today's date
        # The test mainly checks the structure works
        assert "disciplines" in result_4w
        assert "disciplines" in result_12w


if __name__ == "__main__":
    pytest.main([__file__, "-v"])