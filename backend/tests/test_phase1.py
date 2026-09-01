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
import io
import pandas as pd
from datetime import date


@pytest.fixture(scope="function")
def sample_schedule_file():
    df = pd.DataFrame([
        {"activity_code": "PIP-1023", "activity_name": "Erect Line 24-XX-101", "discipline": "Piping", "wbs": "PIP.10.23", "planned_start": date(2026, 8, 15), "planned_finish": date(2026, 8, 30)},
        {"activity_code": "PIP-1027", "activity_name": "Install Support for XX-101", "discipline": "Piping", "wbs": "PIP.10.27", "planned_start": date(2026, 8, 10), "planned_finish": date(2026, 8, 20)},
        {"activity_code": "MEC-2011", "activity_name": "Install Pump P-101", "discipline": "Mechanical", "wbs": "MEC.20.11", "planned_start": date(2026, 8, 25), "planned_finish": date(2026, 9, 5)},
    ])
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return buffer


@pytest.fixture(scope="function")
def sample_progress_excel_file():
    df = pd.DataFrame([
        {"date": date(2026, 8, 30), "discipline": "Piping", "activity_description": "Started erection of XX-101 spool", "status": "Started", "equipment_tag": "XX-101", "location": "Area B", "reported_by": "Supervisor A"},
        {"date": date(2026, 8, 30), "discipline": "Civil", "activity_description": "Foundation A1 concrete pouring in progress", "status": "In Progress", "equipment_tag": "A1", "location": "Area C", "reported_by": "Supervisor B"},
        {"date": date(2026, 8, 29), "discipline": "Mechanical", "activity_description": "Pump P-101 installation completed", "status": "Completed", "equipment_tag": "P-101", "location": "Pump House", "reported_by": "Supervisor C"},
    ])
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return buffer


class TestHealthAndRoot:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "Smarty Vibz API" in response.json()["message"]

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestScheduleUpload:
    def test_valid_schedule_upload(self, client, sample_schedule_file):
        response = client.post("/schedule/upload", files={"file": ("schedule.xlsx", sample_schedule_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 3
        assert data["inserted_rows"] == 3
        assert data["failed_rows"] == 0
        assert len(data["errors"]) == 0

    def test_missing_columns(self, client):
        df = pd.DataFrame([{"activity_code": "PIP-1023", "activity_name": "Test"}])
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        
        response = client.post("/schedule/upload", files={"file": ("schedule.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert response.status_code == 400
        assert "Missing required columns" in response.json()["detail"]

    def test_invalid_date(self, client):
        df = pd.DataFrame([{"activity_code": "PIP-1023", "activity_name": "Test", "discipline": "Piping", "wbs": "PIP.10.23", "planned_start": "invalid", "planned_finish": date(2026, 8, 30)}])
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        
        response = client.post("/schedule/upload", files={"file": ("schedule.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert response.status_code == 200
        data = response.json()
        assert data["failed_rows"] == 1
        assert len(data["errors"]) == 1

    def test_empty_schedule(self, client):
        df = pd.DataFrame(columns=["activity_code", "activity_name", "discipline", "wbs", "planned_start", "planned_finish"])
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        
        response = client.post("/schedule/upload", files={"file": ("schedule.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_get_activities(self, client, sample_schedule_file):
        client.post("/schedule/upload", files={"file": ("schedule.xlsx", sample_schedule_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        response = client.get("/schedule/activities")
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 3
        assert activities[0]["activity_code"] == "MEC-2011"


class TestProgressExtraction:
    def test_valid_progress_extraction(self, client):
        response = client.post("/progress/extract", json={"raw_text": "Today at 9:30 AM, the piping team started erection of the XX-101 spool in Area B"})
        assert response.status_code == 200
        data = response.json()
        assert data["progress_event"]["event_type"] == "START"
        assert data["progress_event"]["activity_reference"] == "XX-101 spool erection"
        assert data["progress_event"]["discipline"] == "Piping"
        assert data["progress_event"]["location"] == "Area B"
        assert data["progress_event"]["equipment_tag"] == "XX-101"
        assert data["progress_event"]["source_type"] == "FREE_TEXT"

    def test_missing_optional_fields(self, client):
        response = client.post("/progress/extract", json={"raw_text": "Work started"})
        assert response.status_code == 200
        data = response.json()
        assert data["progress_event"]["event_type"] == "START"
        assert data["progress_event"]["activity_reference"] is None
        assert data["progress_event"]["discipline"] is None

    def test_empty_progress_report(self, client):
        response = client.post("/progress/extract", json={"raw_text": ""})
        assert response.status_code == 422

    def test_malformed_ai_output_handled(self, client, db_session):
        class BadProvider(MockExtractionProvider):
            def extract_progress(self, raw_text):
                from app.schemas.progress import ProgressEventCreate, SourceType
                return ProgressEventCreate(raw_text=raw_text, event_type="INVALID", source_type=SourceType.FREE_TEXT)
        
        set_extraction_provider(BadProvider())
        response = client.post("/progress/extract", json={"raw_text": "Test"})
        assert response.status_code == 500

    def test_get_progress_events(self, client):
        client.post("/progress/extract", json={"raw_text": "Started XX-101 spool erection"})
        client.post("/progress/extract", json={"raw_text": "Completed pump installation"})
        response = client.get("/progress/events")
        assert response.status_code == 200
        events = response.json()
        assert len(events) == 2


class TestExcelProgressUpload:
    def test_valid_excel_progress_upload(self, client, sample_progress_excel_file):
        response = client.post("/progress/upload-excel", files={"file": ("progress.xlsx", sample_progress_excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 3
        assert data["extracted_events"] == 3
        assert data["failed_rows"] == 0
        
        events_response = client.get("/progress/events")
        events = events_response.json()
        excel_events = [e for e in events if e["source_type"] == "EXCEL"]
        assert len(excel_events) == 3

    def test_excel_progress_missing_optional_columns(self, client):
        df = pd.DataFrame([{"date": date(2026, 8, 30), "activity_description": "Work done", "status": "Started"}])
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        
        response = client.post("/progress/upload-excel", files={"file": ("progress.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert response.status_code == 200
        data = response.json()
        assert data["extracted_events"] == 1

    def test_excel_progress_invalid_date(self, client):
        df = pd.DataFrame([{"date": "invalid", "activity_description": "Work done", "status": "Started"}])
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        
        response = client.post("/progress/upload-excel", files={"file": ("progress.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert response.status_code == 200
        data = response.json()
        assert data["failed_rows"] == 1

    def test_empty_excel_progress_file(self, client):
        df = pd.DataFrame(columns=["date", "activity_description", "status"])
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        
        response = client.post("/progress/upload-excel", files={"file": ("progress.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert response.status_code == 400

    def test_missing_required_columns_excel_progress(self, client):
        df = pd.DataFrame([{"date": date(2026, 8, 30), "activity_description": "Work done"}])
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        
        response = client.post("/progress/upload-excel", files={"file": ("progress.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert response.status_code == 400
        assert "Missing required columns" in response.json()["detail"]


class TestTimeAgent:
    def test_basic_chat(self, client):
        response = client.post("/agent/chat", json={"message": "Today at 9:30 AM, the piping team started erection of the XX-101 spool in Area B", "session_id": "test-session"})
        assert response.status_code == 200
        data = response.json()
        assert data["progress_event_id"] > 0
        assert data["understood"]["activity_reference"] == "XX-101 spool erection"
        assert data["understood"]["event_type"] == "START"
        assert data["understood"]["event_time"] == "09:30"
        assert data["understood"]["location"] == "Area B"
        assert data["understood"]["discipline"] == "Piping"
        assert "logged" in data["reply"].lower()

    def test_extraction_from_natural_language(self, client):
        response = client.post("/agent/chat", json={"message": "Pump P-101 installation is complete", "session_id": "test-session-2"})
        assert response.status_code == 200
        data = response.json()
        assert data["understood"]["event_type"] == "COMPLETE"
        assert data["understood"]["equipment_tag"] == "P-101"

    def test_missing_fields_asks_clarification(self, client):
        response = client.post("/agent/chat", json={"message": "Started work", "session_id": "test-session-3"})
        assert response.status_code == 200
        data = response.json()
        assert data["progress_event_id"] == 0
        assert "missing" in data["reply"].lower()

    def test_multi_turn_conversation_match_it(self, client):
        client.post("/agent/chat", json={"message": "Started XX-101 spool erection at 9:30 AM in Area B", "session_id": "test-session-4"})
        response = client.post("/agent/chat", json={"message": "match it", "session_id": "test-session-4"})
        assert response.status_code == 200
        data = response.json()
        assert data["matched_activity"] is None
        assert "Phase 2" in data["reply"] or "not yet available" in data["reply"]

    def test_multi_turn_show_today(self, client):
        client.post("/agent/chat", json={"message": "Started XX-101 spool erection", "session_id": "test-session-5"})
        response = client.post("/agent/chat", json={"message": "show me what I logged today", "session_id": "test-session-5"})
        assert response.status_code == 200
        data = response.json()
        assert data["progress_event_id"] == 0

    def test_multi_turn_log_another(self, client):
        client.post("/agent/chat", json={"message": "Started XX-101 spool erection", "session_id": "test-session-6"})
        response = client.post("/agent/chat", json={"message": "log another", "session_id": "test-session-6"})
        assert response.status_code == 200
        data = response.json()
        assert data["progress_event_id"] == 0
        assert "ready" in data["reply"].lower()

    def test_hallucination_prevention(self, client):
        response = client.post("/agent/chat", json={"message": "Started work on some unknown thing", "session_id": "test-session-7"})
        assert response.status_code == 200
        data = response.json()
        assert data["understood"]["activity_reference"] is None or "unknown" not in data["understood"]["activity_reference"].lower()

    def test_empty_agent_message(self, client):
        response = client.post("/agent/chat", json={"message": ""})
        assert response.status_code == 422

    def test_get_session_events(self, client):
        client.post("/agent/chat", json={"message": "Started XX-101 spool erection", "session_id": "test-session-8"})
        client.post("/agent/chat", json={"message": "Completed pump installation", "session_id": "test-session-8"})
        response = client.get("/agent/sessions/test-session-8/events")
        assert response.status_code == 200
        events = response.json()
        assert len(events) == 2


class TestDatabaseBehavior:
    def test_schedule_persists(self, client, sample_schedule_file):
        client.post("/schedule/upload", files={"file": ("schedule.xlsx", sample_schedule_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        response = client.get("/schedule/activities")
        assert len(response.json()) == 3
        
        response2 = client.get("/schedule/activities")
        assert len(response2.json()) == 3

    def test_progress_persists(self, client):
        client.post("/progress/extract", json={"raw_text": "Started XX-101"})
        response = client.get("/progress/events")
        assert len(response.json()) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])