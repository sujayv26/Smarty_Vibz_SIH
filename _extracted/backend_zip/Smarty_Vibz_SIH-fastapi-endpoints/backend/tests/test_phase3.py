import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, get_db
from app.models.schedule import ScheduleActivity
from app.models.progress import ProgressEvent
from app.models.confidence import ConfidenceResult, PlannerReview, AuditRecord, ReviewStatus, DecisionType
from app.services.mock_provider import MockExtractionProvider
from app.services.extraction_service import set_extraction_provider
from app.services.confidence_engine import (
    calculate_confidence_score,
    classify_confidence,
    should_auto_match,
    get_confidence_thresholds,
    set_confidence_thresholds,
)
from app.matching.engine import run_matching
from datetime import date, datetime
import json


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
def high_confidence_event(db_session, sample_schedule):
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


@pytest.fixture(scope="function")
def medium_confidence_event(db_session, sample_schedule):
    event = ProgressEvent(
        raw_text="Work started on XX-101 piping",
        activity_reference="XX-101 work",
        event_type="START",
        event_date=date(2026, 8, 30),
        discipline="Piping",
        location="Area B",
        equipment_tag="XX-101",
        source_type="FREE_TEXT",
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture(scope="function")
def low_confidence_event(db_session, sample_schedule):
    event = ProgressEvent(
        raw_text="Some piping work happened",
        event_type="START",
        event_date=date(2026, 8, 30),
        discipline="Piping",
        source_type="FREE_TEXT",
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture(scope="function")
def no_match_event(db_session, sample_schedule):
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
    return event


class TestConfidenceEngine:
    def test_confidence_thresholds_default(self):
        high, medium = get_confidence_thresholds()
        assert high == 0.80
        assert medium == 0.50
    
    def test_confidence_thresholds_custom(self):
        set_confidence_thresholds(0.85, 0.55)
        high, medium = get_confidence_thresholds()
        assert high == 0.85
        assert medium == 0.55
        set_confidence_thresholds(0.80, 0.50)
    
    def test_classify_high(self):
        assert classify_confidence(0.90) == "HIGH"
        assert classify_confidence(0.80) == "HIGH"
    
    def test_classify_medium(self):
        assert classify_confidence(0.70) == "MEDIUM"
        assert classify_confidence(0.50) == "MEDIUM"
    
    def test_classify_low(self):
        assert classify_confidence(0.40) == "LOW"
        assert classify_confidence(0.0) == "LOW"
    
    def test_should_auto_match_high(self):
        assert should_auto_match("HIGH") is True
    
    def test_should_not_auto_match_medium_low(self):
        assert should_auto_match("MEDIUM") is False
        assert should_auto_match("LOW") is False
    
    def test_calculate_confidence_high_event(self, db_session, sample_schedule, high_confidence_event):
        result = run_matching(db_session, high_confidence_event.id)
        score, breakdown = calculate_confidence_score(high_confidence_event, result)
        
        assert 0.0 <= score <= 1.0
        assert breakdown.exact_identifier_strength >= 0
        assert breakdown.fuzzy_similarity >= 0
        assert breakdown.semantic_similarity >= 0
        assert breakdown.discipline_compatibility >= 0
        assert breakdown.context_compatibility >= 0
        assert breakdown.temporal_compatibility >= 0
        assert breakdown.missing_information_penalty >= 0
        assert breakdown.candidate_ambiguity_penalty >= 0
    
    def test_calculate_confidence_no_match(self, db_session, sample_schedule, no_match_event):
        result = run_matching(db_session, no_match_event.id)
        score, breakdown = calculate_confidence_score(no_match_event, result)
        
        assert score == 0.0
        assert breakdown.missing_information_penalty == 1.0
    
    def test_confidence_deterministic(self, db_session, sample_schedule, high_confidence_event):
        result = run_matching(db_session, high_confidence_event.id)
        score1, _ = calculate_confidence_score(high_confidence_event, result)
        score2, _ = calculate_confidence_score(high_confidence_event, result)
        assert score1 == score2


class TestConfidenceAPI:
    def test_evaluate_confidence_high_auto_match(self, client, db_session, sample_schedule, high_confidence_event):
        response = client.post(f"/confidence/evaluate/{high_confidence_event.id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["progress_event_id"] == high_confidence_event.id
        assert data["confidence_score"] >= 0.0
        assert data["confidence_level"] in ["HIGH", "MEDIUM", "LOW"]
        assert data["decision"] in ["AUTO_MATCH", "REVIEW_REQUIRED"]
        assert "requires_review" in data
        assert "score_breakdown" in data
        assert "top_candidates" in data
    
    def test_evaluate_confidence_medium_creates_review(self, client, db_session, sample_schedule, medium_confidence_event):
        response = client.post(f"/confidence/evaluate/{medium_confidence_event.id}")
        assert response.status_code == 200
        data = response.json()
        
        if data["confidence_level"] in ["MEDIUM", "LOW"]:
            assert data["decision"] == "REVIEW_REQUIRED"
            assert data["requires_review"] is True
            assert data["review_id"] is not None
            
            review_id = data["review_id"]
            review_response = client.get(f"/reviews/{review_id}")
            assert review_response.status_code == 200
            review_data = review_response.json()
            assert review_data["status"] == "PENDING"
            assert review_data["review_id"] == review_id
    
    def test_evaluate_confidence_duplicate_error(self, client, db_session, sample_schedule, high_confidence_event):
        client.post(f"/confidence/evaluate/{high_confidence_event.id}")
        response = client.post(f"/confidence/evaluate/{high_confidence_event.id}")
        assert response.status_code == 400
        assert "already evaluated" in response.json()["detail"]
    
    def test_evaluate_confidence_not_found(self, client):
        response = client.post("/confidence/evaluate/99999")
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]
    
    def test_evaluate_confidence_invalid_progress_event(self, client, db_session, sample_schedule):
        event = ProgressEvent(
            raw_text="Test work",
            event_type="START",
            event_date=date(2026, 8, 30),
            discipline="Piping",
            source_type="FREE_TEXT",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        
        response = client.post(f"/confidence/evaluate/{event.id}")
        assert response.status_code == 200


class TestPlannerReview:
    def test_get_pending_reviews(self, client, db_session, sample_schedule, medium_confidence_event):
        client.post(f"/confidence/evaluate/{medium_confidence_event.id}")
        
        response = client.get("/reviews/pending")
        assert response.status_code == 200
        data = response.json()
        assert "reviews" in data
        assert len(data["reviews"]) >= 1
        
        review = data["reviews"][0]
        assert review["status"] == "PENDING"
        assert review["progress_event_id"] == medium_confidence_event.id
        assert review["confidence_level"] in ["MEDIUM", "LOW"]
        assert "top_candidates" in review
        assert "score_breakdown" in review
        assert "matching_reasons" in review
    
    def test_get_review_by_id(self, client, db_session, sample_schedule, medium_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{medium_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        response = client.get(f"/reviews/{review_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["review_id"] == review_id
        assert data["status"] == "PENDING"
    
    def test_get_review_not_found(self, client):
        response = client.get("/reviews/99999")
        assert response.status_code == 404
    
    def test_approve_review(self, client, db_session, sample_schedule, medium_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{medium_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        response = client.post(f"/reviews/{review_id}/approve", json={"reviewer_note": "Looks good"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["reviewer_note"] == "Looks good"
        assert data["completed_at"] is not None
        
        audit_response = client.get(f"/audit/{medium_confidence_event.id}")
        assert audit_response.status_code == 200
        audit_data = audit_response.json()
        assert len(audit_data["audit_records"]) >= 1
        assert any(r["decision"] == "APPROVED" for r in audit_data["audit_records"])
    
    def test_approve_already_completed_review(self, client, db_session, sample_schedule, medium_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{medium_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        client.post(f"/reviews/{review_id}/approve", json={})
        response = client.post(f"/reviews/{review_id}/approve", json={})
        assert response.status_code == 400
        assert "not pending" in response.json()["detail"]
    
    def test_correct_review(self, client, db_session, sample_schedule, medium_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{medium_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        pip1027 = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1027").first()
        
        response = client.post(f"/reviews/{review_id}/correct", json={"activity_id": pip1027.id, "reviewer_note": "Corrected to support"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CORRECTED"
        assert data["reviewer_note"] == "Corrected to support"
        
        audit_response = client.get(f"/audit/{medium_confidence_event.id}")
        audit_data = audit_response.json()
        assert any(r["decision"] == "CORRECTED" for r in audit_data["audit_records"])
    
    def test_correct_invalid_activity(self, client, db_session, sample_schedule, medium_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{medium_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        response = client.post(f"/reviews/{review_id}/correct", json={"activity_id": 99999})
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]
    
    def test_correct_completed_review(self, client, db_session, sample_schedule, medium_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{medium_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        pip1027 = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1027").first()
        client.post(f"/reviews/{review_id}/approve", json={})
        response = client.post(f"/reviews/{review_id}/correct", json={"activity_id": pip1027.id})
        assert response.status_code == 400
        assert "not pending" in response.json()["detail"]
    
    def test_reject_review(self, client, db_session, sample_schedule, medium_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{medium_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        response = client.post(f"/reviews/{review_id}/reject", json={"reviewer_note": "Not a match"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"
        assert data["reviewer_note"] == "Not a match"
        
        audit_response = client.get(f"/audit/{medium_confidence_event.id}")
        audit_data = audit_response.json()
        assert any(r["decision"] == "REJECTED" for r in audit_data["audit_records"])
    
    def test_reject_completed_review(self, client, db_session, sample_schedule, medium_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{medium_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        client.post(f"/reviews/{review_id}/approve", json={})
        response = client.post(f"/reviews/{review_id}/reject", json={})
        assert response.status_code == 400
        assert "not pending" in response.json()["detail"]
    
    def test_create_new_activity(self, client, db_session, sample_schedule, low_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{low_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        response = client.post(f"/reviews/{review_id}/create-new", json={
            "activity_code": "MISC-9001",
            "activity_name": "Repaint perimeter fence",
            "discipline": "Civil",
            "wbs": "MISC.9001",
            "reviewer_note": "This work was not in the original schedule"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "NEW_ACTIVITY_CREATED"
        
        new_activity = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "MISC-9001").first()
        assert new_activity is not None
        assert new_activity.is_unplanned is True
        assert new_activity.activity_name == "Repaint perimeter fence"
        assert new_activity.discipline == "Civil"
        
        audit_response = client.get(f"/audit/{low_confidence_event.id}")
        audit_data = audit_response.json()
        assert any(r["decision"] == "NEW_ACTIVITY_CREATED" for r in audit_data["audit_records"])
        assert any(r["new_activity_id"] is not None for r in audit_data["audit_records"])
    
    def test_create_new_activity_duplicate_code(self, client, db_session, sample_schedule, low_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{low_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        response = client.post(f"/reviews/{review_id}/create-new", json={
            "activity_code": "PIP-1023",
            "activity_name": "Duplicate",
            "discipline": "Piping",
        })
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_create_new_activity_empty_code(self, client, db_session, sample_schedule, low_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{low_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        response = client.post(f"/reviews/{review_id}/create-new", json={
            "activity_code": "",
            "activity_name": "Test",
            "discipline": "Civil",
        })
        assert response.status_code == 422
        detail = response.json()["detail"]
        if isinstance(detail, list):
            detail = " ".join(str(d) for d in detail)
        assert "cannot be empty" in detail.lower()
    
    def test_create_new_activity_missing_name(self, client, db_session, sample_schedule, low_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{low_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        response = client.post(f"/reviews/{review_id}/create-new", json={
            "activity_code": "MISC-9002",
            "activity_name": "",
            "discipline": "Civil",
        })
        assert response.status_code == 422
        detail = response.json()["detail"]
        if isinstance(detail, list):
            detail = " ".join(str(d) for d in detail)
        assert "cannot be empty" in detail.lower()
    
    def test_create_new_activity_missing_discipline(self, client, db_session, sample_schedule, low_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{low_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        response = client.post(f"/reviews/{review_id}/create-new", json={
            "activity_code": "MISC-9003",
            "activity_name": "Test",
            "discipline": "",
        })
        assert response.status_code == 422
        detail = response.json()["detail"]
        if isinstance(detail, list):
            detail = " ".join(str(d) for d in detail)
        assert "cannot be empty" in detail.lower()
    
    def test_create_new_activity_completed_review(self, client, db_session, sample_schedule, low_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{low_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        
        client.post(f"/reviews/{review_id}/approve", json={})
        response = client.post(f"/reviews/{review_id}/create-new", json={
            "activity_code": "MISC-9004",
            "activity_name": "Test",
            "discipline": "Civil",
        })
        assert response.status_code == 400
        assert "not pending" in response.json()["detail"]


class TestAuditTrail:
    def test_audit_auto_match(self, client, db_session, sample_schedule, high_confidence_event):
        response = client.post(f"/confidence/evaluate/{high_confidence_event.id}")
        assert response.status_code == 200
        
        if response.json()["decision"] == "AUTO_MATCH":
            audit_response = client.get(f"/audit/{high_confidence_event.id}")
            assert audit_response.status_code == 200
            audit_data = audit_response.json()
            assert len(audit_data["audit_records"]) == 1
            assert audit_data["audit_records"][0]["decision"] == "AUTO_MATCH"
            assert audit_data["audit_records"][0]["actor_type"] == "SYSTEM"
            assert audit_data["audit_records"][0]["final_activity_id"] is not None
    
    def test_audit_approve(self, client, db_session, sample_schedule, medium_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{medium_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        client.post(f"/reviews/{review_id}/approve", json={"reviewer_note": "Approved"})
        
        audit_response = client.get(f"/audit/{medium_confidence_event.id}")
        audit_data = audit_response.json()
        assert any(r["decision"] == "APPROVED" for r in audit_data["audit_records"])
        assert any(r["actor_type"] == "PLANNER" for r in audit_data["audit_records"])
        assert any(r["reviewer_note"] == "Approved" for r in audit_data["audit_records"])
    
    def test_audit_correct(self, client, db_session, sample_schedule, medium_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{medium_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        pip1027 = db_session.query(ScheduleActivity).filter(ScheduleActivity.activity_code == "PIP-1027").first()
        client.post(f"/reviews/{review_id}/correct", json={"activity_id": pip1027.id})
        
        audit_response = client.get(f"/audit/{medium_confidence_event.id}")
        audit_data = audit_response.json()
        assert any(r["decision"] == "CORRECTED" for r in audit_data["audit_records"])
        assert any(r["actor_type"] == "PLANNER" for r in audit_data["audit_records"])
    
    def test_audit_reject(self, client, db_session, sample_schedule, medium_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{medium_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        client.post(f"/reviews/{review_id}/reject", json={"reviewer_note": "Rejected"})
        
        audit_response = client.get(f"/audit/{medium_confidence_event.id}")
        audit_data = audit_response.json()
        assert any(r["decision"] == "REJECTED" for r in audit_data["audit_records"])
        assert any(r["final_activity_id"] is None for r in audit_data["audit_records"])
    
    def test_audit_new_activity_created(self, client, db_session, sample_schedule, low_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{low_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        client.post(f"/reviews/{review_id}/create-new", json={
            "activity_code": "MISC-9005",
            "activity_name": "New test activity",
            "discipline": "Civil",
        })
        
        audit_response = client.get(f"/audit/{low_confidence_event.id}")
        audit_data = audit_response.json()
        assert any(r["decision"] == "NEW_ACTIVITY_CREATED" for r in audit_data["audit_records"])
        assert any(r["new_activity_id"] is not None for r in audit_data["audit_records"])
        assert any(r["actor_type"] == "PLANNER" for r in audit_data["audit_records"])


class TestNewActivityFutureMatching:
    def test_new_activity_participates_in_future_matching(self, client, db_session, sample_schedule, low_confidence_event):
        eval_response = client.post(f"/confidence/evaluate/{low_confidence_event.id}")
        review_id = eval_response.json()["review_id"]
        client.post(f"/reviews/{review_id}/create-new", json={
            "activity_code": "MISC-9006",
            "activity_name": "Future matching test",
            "discipline": "Civil",
        })
        
        new_event = ProgressEvent(
            raw_text="Future matching test activity started",
            event_type="START",
            event_date=date(2026, 9, 1),
            discipline="Civil",
            source_type="FREE_TEXT",
        )
        db_session.add(new_event)
        db_session.commit()
        db_session.refresh(new_event)
        
        match_response = client.post(f"/matching/run/{new_event.id}")
        assert match_response.status_code == 200
        match_data = match_response.json()
        assert len(match_data["top_matches"]) > 0
        found = any(m["activity_code"] == "MISC-9006" for m in match_data["top_matches"])
        assert found


class TestPhase1And2StillWork:
    def test_schedule_upload_still_works(self, client):
        import io
        import pandas as pd
        
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
    
    def test_matching_still_works(self, client, db_session, sample_schedule):
        event = ProgressEvent(
            raw_text="Started erection of XX-101 spool",
            event_type="START",
            event_date=date(2026, 8, 30),
            discipline="Piping",
            equipment_tag="XX-101",
            source_type="FREE_TEXT",
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        
        response = client.post(f"/matching/run/{event.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["progress_event_id"] == event.id
        assert len(data["top_matches"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])