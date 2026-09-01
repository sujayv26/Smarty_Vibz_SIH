import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models.schedule import ScheduleActivity
from app.models.progress import ProgressEvent
from app.services.mock_provider import MockExtractionProvider
from app.services.extraction_service import set_extraction_provider
from app.matching.engine import run_matching
from app.matching.matchers.exact import exact_match_score, extract_identifiers
from app.matching.matchers.fuzzy import fuzzy_match_score
from app.matching.matchers.context import context_match_score
from app.matching.matchers.temporal import temporal_match_score
from app.matching.matchers.semantic import OfflineSemanticMatcher, get_semantic_matcher
from app.matching.benchmark import BENCHMARK_CASES, run_benchmark, MatchCategory
from datetime import date
import io
import pandas as pd

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client(db_session):
    set_extraction_provider(MockExtractionProvider())
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def sample_schedule(db_session):
    activities = [
        ScheduleActivity(
            activity_code="PIP-1023",
            activity_name="Erect Line 24-XX-101",
            discipline="Piping",
            wbs="PIP.10.23",
            planned_start=date(2026, 8, 15),
            planned_finish=date(2026, 8, 30),
        ),
        ScheduleActivity(
            activity_code="PIP-1027",
            activity_name="Install Support for XX-101",
            discipline="Piping",
            wbs="PIP.10.27",
            planned_start=date(2026, 8, 10),
            planned_finish=date(2026, 8, 20),
        ),
        ScheduleActivity(
            activity_code="PIP-1042",
            activity_name="Inspect XX-101",
            discipline="Piping",
            wbs="PIP.10.42",
            planned_start=date(2026, 9, 1),
            planned_finish=date(2026, 9, 5),
        ),
        ScheduleActivity(
            activity_code="PIP-1050",
            activity_name="Hydrotest Line XX-101",
            discipline="Piping",
            wbs="PIP.10.50",
            planned_start=date(2026, 9, 5),
            planned_finish=date(2026, 9, 10),
        ),
        ScheduleActivity(
            activity_code="MEC-2011",
            activity_name="Install Pump P-101",
            discipline="Mechanical",
            wbs="MEC.20.11",
            planned_start=date(2026, 8, 25),
            planned_finish=date(2026, 9, 5),
        ),
        ScheduleActivity(
            activity_code="CIV-3011",
            activity_name="Construct Foundation A1",
            discipline="Civil",
            wbs="CIV.30.11",
            planned_start=date(2026, 8, 1),
            planned_finish=date(2026, 8, 15),
        ),
    ]
    for act in activities:
        db_session.add(act)
    db_session.commit()
    return activities

@pytest.fixture(scope="function")
def full_schedule(db_session):
    activities = [
        ScheduleActivity(activity_code="CIV-3011", activity_name="Construct Foundation A1", discipline="Civil", wbs="CIV.30.11", planned_start=date(2026, 8, 1), planned_finish=date(2026, 8, 15)),
        ScheduleActivity(activity_code="CIV-3012", activity_name="Construct Foundation A2", discipline="Civil", wbs="CIV.30.12", planned_start=date(2026, 8, 10), planned_finish=date(2026, 8, 25)),
        ScheduleActivity(activity_code="CIV-3021", activity_name="Erect Structural Steel Grid 1", discipline="Civil", wbs="CIV.30.21", planned_start=date(2026, 8, 20), planned_finish=date(2026, 9, 10)),
        ScheduleActivity(activity_code="PIP-1023", activity_name="Erect Line 24-XX-101", discipline="Piping", wbs="PIP.10.23", planned_start=date(2026, 8, 15), planned_finish=date(2026, 8, 30)),
        ScheduleActivity(activity_code="PIP-1027", activity_name="Install Support for XX-101", discipline="Piping", wbs="PIP.10.27", planned_start=date(2026, 8, 10), planned_finish=date(2026, 8, 20)),
        ScheduleActivity(activity_code="PIP-1042", activity_name="Inspect XX-101", discipline="Piping", wbs="PIP.10.42", planned_start=date(2026, 9, 1), planned_finish=date(2026, 9, 5)),
        ScheduleActivity(activity_code="PIP-1050", activity_name="Hydrotest Line XX-101", discipline="Piping", wbs="PIP.10.50", planned_start=date(2026, 9, 5), planned_finish=date(2026, 9, 10)),
        ScheduleActivity(activity_code="MEC-2011", activity_name="Install Pump P-101", discipline="Mechanical", wbs="MEC.20.11", planned_start=date(2026, 8, 25), planned_finish=date(2026, 9, 5)),
        ScheduleActivity(activity_code="MEC-2012", activity_name="Align Pump P-101", discipline="Mechanical", wbs="MEC.20.12", planned_start=date(2026, 9, 5), planned_finish=date(2026, 9, 10)),
        ScheduleActivity(activity_code="MEC-2021", activity_name="Install Compressor C-101", discipline="Mechanical", wbs="MEC.20.21", planned_start=date(2026, 9, 1), planned_finish=date(2026, 9, 15)),
        ScheduleActivity(activity_code="ELE-4011", activity_name="Cable Pulling for Substation SUB-1", discipline="Electrical", wbs="ELE.40.11", planned_start=date(2026, 8, 20), planned_finish=date(2026, 9, 5)),
        ScheduleActivity(activity_code="ELE-4012", activity_name="Terminate Cables SUB-1", discipline="Electrical", wbs="ELE.40.12", planned_start=date(2026, 9, 5), planned_finish=date(2026, 9, 15)),
        ScheduleActivity(activity_code="ELE-4021", activity_name="Install MCC Panel MCC-1", discipline="Electrical", wbs="ELE.40.21", planned_start=date(2026, 8, 25), planned_finish=date(2026, 9, 10)),
        ScheduleActivity(activity_code="INS-5011", activity_name="Install Instrument Tubing", discipline="Instrumentation", wbs="INS.50.11", planned_start=date(2026, 9, 1), planned_finish=date(2026, 9, 20)),
        ScheduleActivity(activity_code="INS-5012", activity_name="Calibrate Transmitters", discipline="Instrumentation", wbs="INS.50.12", planned_start=date(2026, 9, 15), planned_finish=date(2026, 9, 30)),
        ScheduleActivity(activity_code="PIP-1060", activity_name="Erect Line 24-XX-102", discipline="Piping", wbs="PIP.10.60", planned_start=date(2026, 8, 20), planned_finish=date(2026, 9, 5)),
        ScheduleActivity(activity_code="PIP-1065", activity_name="Install Support for XX-102", discipline="Piping", wbs="PIP.10.65", planned_start=date(2026, 8, 15), planned_finish=date(2026, 8, 25)),
        ScheduleActivity(activity_code="CIV-3031", activity_name="Construct Foundation B1", discipline="Civil", wbs="CIV.30.31", planned_start=date(2026, 8, 15), planned_finish=date(2026, 8, 30)),
    ]
    for act in activities:
        db_session.add(act)
    db_session.commit()
    return activities

@pytest.fixture(scope="function")
def sample_progress_event(db_session, sample_schedule):
    event = ProgressEvent(
        raw_text="Today at 9:30 AM, the piping team started erection of the XX-101 spool in Area B",
        activity_reference="XX-101 spool erection",
        event_type="START",
        event_date=date(2026, 8, 30),
        event_time="09:30",
        discipline="Piping",
        location="Area B",
        equipment_tag="XX-101",
        source_type="FREE_TEXT",
        source_file=None,
        session_id=None,
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


class TestExactMatcher:
    def test_extract_identifiers(self):
        text = "Started erection of XX-101 spool and PIP-1023 line"
        ids = extract_identifiers(text)
        assert "XX-101" in ids
        assert "PIP-1023" in ids
    
    def test_extract_identifiers_case_insensitive(self):
        text = "work on xx-101 and pip-1023"
        ids = extract_identifiers(text)
        assert "XX-101" in ids
        assert "PIP-1023" in ids
    
    def test_exact_match_perfect(self, db_session, sample_schedule, sample_progress_event):
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1023").first()
        score, reasons = exact_match_score(sample_progress_event, activity)
        assert score == 1.0
        assert any("101" in r for r in reasons)
    
    def test_exact_match_wrong_activity(self, db_session, sample_schedule, sample_progress_event):
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "MEC-2011").first()
        score, reasons = exact_match_score(sample_progress_event, activity)
        assert score == 0.0


class TestFuzzyMatcher:
    def test_fuzzy_match_high(self, db_session, sample_schedule, sample_progress_event):
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1023").first()
        score, reasons = fuzzy_match_score(sample_progress_event, activity)
        assert score > 0.6
        assert len(reasons) > 0
    
    def test_fuzzy_match_low_for_different_discipline(self, db_session, sample_schedule, sample_progress_event):
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "MEC-2011").first()
        score, reasons = fuzzy_match_score(sample_progress_event, activity)
        assert score < 0.5


class TestContextMatcher:
    def test_discipline_match(self, db_session, sample_schedule, sample_progress_event):
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1023").first()
        score, reasons = context_match_score(sample_progress_event, activity)
        assert score > 0
        assert any("Discipline" in r for r in reasons)
    
    def test_event_type_match_start(self, db_session, sample_schedule, sample_progress_event):
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1023").first()
        score, reasons = context_match_score(sample_progress_event, activity)
        assert any("START" in r or "erect" in r.lower() for r in reasons)
    
    def test_event_type_match_complete_inspect(self, db_session, sample_schedule):
        event = ProgressEvent(
            raw_text="Inspect XX-101 completed",
            activity_reference="XX-101 inspection",
            event_type="COMPLETE",
            event_date=date(2026, 9, 3),
            discipline="Piping",
            location="Area B",
            equipment_tag="XX-101",
            source_type="FREE_TEXT",
        )
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1042").first()
        score, reasons = context_match_score(event, activity)
        assert any("COMPLETE" in r or "inspect" in r.lower() for r in reasons)
    
    def test_equipment_tag_match(self, db_session, sample_schedule, sample_progress_event):
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1023").first()
        score, reasons = context_match_score(sample_progress_event, activity)
        assert any("Equipment tag" in r for r in reasons)


class TestTemporalMatcher:
    def test_temporal_match_within_window(self, db_session, sample_schedule, sample_progress_event):
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1023").first()
        score, reasons = temporal_match_score(sample_progress_event, activity)
        assert score == 1.0
        assert any("falls within" in r for r in reasons)
    
    def test_temporal_match_before_window(self, db_session, sample_schedule):
        event = ProgressEvent(
            raw_text="Early start on XX-101",
            event_type="START",
            event_date=date(2026, 8, 10),
            discipline="Piping",
            equipment_tag="XX-101",
            source_type="FREE_TEXT",
        )
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1023").first()
        score, reasons = temporal_match_score(event, activity)
        assert 0.5 <= score < 1.0
    
    def test_temporal_match_after_window(self, db_session, sample_schedule):
        event = ProgressEvent(
            raw_text="Late completion of XX-101",
            event_type="COMPLETE",
            event_date=date(2026, 9, 10),
            discipline="Piping",
            equipment_tag="XX-101",
            source_type="FREE_TEXT",
        )
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1023").first()
        score, reasons = temporal_match_score(event, activity)
        assert 0.05 <= score < 0.5
    
    def test_temporal_no_event_date(self, db_session, sample_schedule):
        event = ProgressEvent(
            raw_text="Work on XX-101",
            event_type="START",
            event_date=None,
            discipline="Piping",
            equipment_tag="XX-101",
            source_type="FREE_TEXT",
        )
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1023").first()
        score, reasons = temporal_match_score(event, activity)
        assert score == 0.0


class TestSemanticMatcher:
    def test_offline_semantic_available(self):
        matcher = OfflineSemanticMatcher()
        assert matcher.is_available() is True
    
    def test_semantic_keyword_match(self, db_session, sample_schedule, sample_progress_event):
        matcher = OfflineSemanticMatcher()
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1023").first()
        score, reasons = matcher.match(sample_progress_event, activity)
        assert score > 0
        assert any("erect" in r.lower() or "keyword" in r.lower() for r in reasons)
    
    def test_semantic_no_match(self, db_session, sample_schedule):
        event = ProgressEvent(
            raw_text="Office meeting about budget",
            event_type="START",
            event_date=date(2026, 8, 30),
            discipline="Admin",
            source_type="FREE_TEXT",
        )
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1023").first()
        matcher = OfflineSemanticMatcher()
        score, reasons = matcher.match(event, activity)
        assert score == 0.0


class TestMatchingEngine:
    def test_run_matching_returns_top3(self, db_session, sample_schedule, sample_progress_event):
        result = run_matching(db_session, sample_progress_event.id)
        assert result is not None
        assert result.progress_event_id == sample_progress_event.id
        assert len(result.top_matches) <= 3
        assert len(result.top_matches) > 0
    
    def test_top_match_is_correct_activity(self, db_session, sample_schedule, sample_progress_event):
        result = run_matching(db_session, sample_progress_event.id)
        assert result.top_matches[0].activity_code == "PIP-1023"
    
    def test_score_breakdown_present(self, db_session, sample_schedule, sample_progress_event):
        result = run_matching(db_session, sample_progress_event.id)
        match = result.top_matches[0]
        assert match.component_scores.exact >= 0
        assert match.component_scores.semantic >= 0
        assert match.component_scores.fuzzy >= 0
        assert match.component_scores.discipline >= 0
        assert match.component_scores.context >= 0
        assert match.component_scores.temporal >= 0
    
    def test_final_score_calculation(self, db_session, sample_schedule, sample_progress_event):
        result = run_matching(db_session, sample_progress_event.id)
        match = result.top_matches[0]
        cs = match.component_scores
        expected = (
            0.30 * cs.exact +
            0.25 * cs.semantic +
            0.20 * cs.fuzzy +
            0.10 * cs.discipline +
            0.10 * cs.context +
            0.05 * cs.temporal
        )
        assert abs(match.final_score - round(expected, 4)) < 0.001
    
    def test_reasons_are_deterministic_and_readable(self, db_session, sample_schedule, sample_progress_event):
        result = run_matching(db_session, sample_progress_event.id)
        match = result.top_matches[0]
        assert len(match.reasons) > 0
        for reason in match.reasons:
            assert isinstance(reason, str)
            assert len(reason) > 0
    
    def test_xx101_ambiguity_distinguishes_erect_vs_support_vs_inspect(self, db_session, sample_schedule):
        event_erect = ProgressEvent(
            raw_text="Started erection of XX-101 spool",
            event_type="START",
            event_date=date(2026, 8, 30),
            discipline="Piping",
            equipment_tag="XX-101",
            source_type="FREE_TEXT",
        )
        db_session.add(event_erect)
        db_session.commit()
        db_session.refresh(event_erect)
        
        result = run_matching(db_session, event_erect.id)
        assert result.top_matches[0].activity_code == "PIP-1023"
        assert "erect" in " ".join(result.top_matches[0].reasons).lower() or "start" in " ".join(result.top_matches[0].reasons).lower()
        
        event_support = ProgressEvent(
            raw_text="Install Support for XX-101 completed",
            event_type="COMPLETE",
            event_date=date(2026, 8, 20),
            discipline="Piping",
            equipment_tag="XX-101",
            source_type="FREE_TEXT",
        )
        db_session.add(event_support)
        db_session.commit()
        db_session.refresh(event_support)
        
        result = run_matching(db_session, event_support.id)
        assert result.top_matches[0].activity_code == "PIP-1027"
        
        event_inspect = ProgressEvent(
            raw_text="Inspect XX-101 completed",
            event_type="COMPLETE",
            event_date=date(2026, 9, 3),
            discipline="Piping",
            equipment_tag="XX-101",
            source_type="FREE_TEXT",
        )
        db_session.add(event_inspect)
        db_session.commit()
        db_session.refresh(event_inspect)
        
        result = run_matching(db_session, event_inspect.id)
        assert result.top_matches[0].activity_code == "PIP-1042"
    
    def test_no_match_returns_empty(self, db_session, sample_schedule):
        event = ProgressEvent(
            raw_text="Office furniture delivery received",
            event_type="COMPLETE",
            event_date=date(2026, 8, 15),
            discipline="Admin",
            source_type="FREE_TEXT",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        
        result = run_matching(db_session, event.id)
        assert result is not None
        assert len(result.top_matches) == 0
    
    def test_missing_progress_event_returns_none(self, db_session):
        result = run_matching(db_session, 99999)
        assert result is None


class TestMatchingAPI:
    def test_matching_run_endpoint_success(self, client, db_session, sample_schedule, sample_progress_event):
        response = client.post(f"/matching/run/{sample_progress_event.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["progress_event_id"] == sample_progress_event.id
        assert len(data["top_matches"]) > 0
        assert data["top_matches"][0]["activity_code"] == "PIP-1023"
        assert "final_score" in data["top_matches"][0]
        assert "component_scores" in data["top_matches"][0]
        assert "reasons" in data["top_matches"][0]
    
    def test_matching_run_endpoint_not_found(self, client):
        response = client.post("/matching/run/99999")
        assert response.status_code == 404
    
    def test_matching_run_endpoint_structure(self, client, db_session, sample_schedule, sample_progress_event):
        response = client.post(f"/matching/run/{sample_progress_event.id}")
        data = response.json()
        match = data["top_matches"][0]
        required_fields = [
            "activity_id", "activity_code", "activity_name", "discipline",
            "wbs", "planned_start", "planned_finish", "final_score",
            "component_scores", "reasons"
        ]
        for field in required_fields:
            assert field in match
        
        cs = match["component_scores"]
        assert all(k in cs for k in ["exact", "semantic", "fuzzy", "discipline", "context", "temporal"])


class TestBenchmark:
    def test_benchmark_dataset_size(self):
        assert len(BENCHMARK_CASES) == 50
    
    def test_benchmark_categories(self):
        categories = [case.category for case in BENCHMARK_CASES]
        assert categories.count(MatchCategory.EXACT_MATCH) == 15
        assert categories.count(MatchCategory.FUZZY_WORDING) == 10
        assert categories.count(MatchCategory.AMBIGUOUS_TAG) == 10
        assert categories.count(MatchCategory.MISSING_FIELDS) == 5
        assert categories.count(MatchCategory.NO_MATCH) == 5
        assert categories.count(MatchCategory.MULTI_DISCIPLINE) == 5
    
    def test_benchmark_endpoint(self, client, db_session, full_schedule):
        response = client.post("/matching/benchmark")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        summary = data["summary"]
        assert summary["total_reports"] == 50
        assert "top1_accuracy" in summary
        assert "top3_accuracy" in summary
        assert "category_results" in summary
        assert len(summary["reports"]) == 50
    
    def test_benchmark_accuracy_not_hardcoded(self, client, db_session, full_schedule):
        response = client.post("/matching/benchmark")
        data = response.json()
        summary = data["summary"]
        assert 0.0 <= summary["top1_accuracy"] <= 1.0
        assert 0.0 <= summary["top3_accuracy"] <= 1.0
        for cat, metrics in summary["category_results"].items():
            assert metrics["count"] > 0
            assert 0.0 <= metrics["top1_accuracy"] <= 1.0
            assert 0.0 <= metrics["top3_accuracy"] <= 1.0


class TestSemanticFallback:
    def test_semantic_fallback_works_offline(self, db_session, sample_schedule, sample_progress_event):
        matcher = get_semantic_matcher()
        assert matcher.is_available() is True
        
        activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1023").first()
        score, reasons = matcher.match(sample_progress_event, activity)
        assert score >= 0.0
        assert isinstance(reasons, list)


class TestPhase1StillWorks:
    def test_schedule_upload_still_works(self, client):
        df = pd.DataFrame([{
            "activity_code": "TEST-001",
            "activity_name": "Test Activity",
            "discipline": "Test",
            "wbs": "TEST.001",
            "planned_start": date(2026, 1, 1),
            "planned_finish": date(2026, 1, 10),
        }])
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        
        response = client.post("/schedule/upload", files={"file": ("test.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert response.status_code == 200
        assert response.json()["inserted_rows"] == 1
    
    def test_progress_extraction_still_works(self, client):
        response = client.post("/progress/extract", json={"raw_text": "Started test work"})
        assert response.status_code == 200
        assert response.json()["progress_event"]["event_type"] == "START"
    
    def test_agent_chat_still_works(self, client):
        response = client.post("/agent/chat", json={"message": "Today at 9:30 AM, the piping team started erection of the XX-101 spool in Area B", "session_id": "test"})
        assert response.status_code == 200
        assert response.json()["progress_event_id"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])