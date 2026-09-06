import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.services.mock_provider import MockExtractionProvider
from app.services.extraction_service import set_extraction_provider
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.ingestion_source import IngestionSource
from app.core.security import get_password_hash, create_access_token

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply the database override for all tests
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


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
def test_org(db_session):
    org = Organization(name="Test Org", slug="test", description="Test organization")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="function")
def test_project(db_session, test_org):
    project = Project(
        name="Test Project",
        code="TEST-001",
        description="Test project",
        organization_id=test_org.id,
        location="Test City",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture(scope="function")
def test_user(db_session, test_org, test_project):
    user = User(
        email="test@test.com",
        hashed_password=get_password_hash("test123"),
        full_name="Test User",
        role=UserRole.SITE_SUPERVISOR,
        organization_id=test_org.id,
        discipline="Civil",
        preferred_language="en",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_supervisor(db_session, test_org, test_project):
    user = User(
        email="supervisor@test.com",
        hashed_password=get_password_hash("supervisor123"),
        full_name="Test Supervisor",
        role=UserRole.SITE_SUPERVISOR,
        organization_id=test_org.id,
        discipline="Civil",
        preferred_language="en",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    access_token = create_access_token(data={"sub": str(test_user.id), "role": test_user.role.value, "org_id": test_user.organization_id})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="function")
def auth_cookies(test_user):
    access_token = create_access_token(data={"sub": str(test_user.id), "role": test_user.role.value, "org_id": test_user.organization_id})
    return {"access_token": access_token}


@pytest.fixture(scope="function")
def client(db_session, test_org, test_project, test_supervisor):
    set_extraction_provider(MockExtractionProvider())
    
    # Create ingestion sources
    sources = [
        ("VOICE", "Voice/Time-Agent", "Supervisor voice notes"),
        ("TIME_AGENT", "Time-Agent Chat", "Conversational Time-Agent chat"),
        ("TEXT_DIARY", "Text Diary", "Manual text diary entries"),
        ("SPREADSHEET", "Spreadsheet Upload", "Excel/CSV progress uploads"),
        ("PDF_OCR", "PDF/OCR Scan", "Scanned daily diaries via OCR"),
        ("PMIS_EXPORT", "PMIS Export", "Automated PMIS schedule exports"),
        ("WHATSAPP", "WhatsApp", "WhatsApp Business Cloud API messages"),
    ]
    for code, name, desc in sources:
        src = IngestionSource(code=code, name=name, description=desc)
        db_session.add(src)
    db_session.commit()
    
    # Create access token for Authorization header (works with multipart uploads)
    access_token = create_access_token(data={"sub": str(test_supervisor.id), "role": test_supervisor.role.value, "org_id": test_supervisor.organization_id})
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    # Wrapper to add auth headers to all requests
    class AuthenticatedClient:
        def __init__(self, client, headers):
            self._client = client
            self._headers = headers
        
        def _merge_headers(self, headers):
            if headers:
                merged = self._headers.copy()
                merged.update(headers)
                return merged
            return self._headers
        
        def get(self, url, **kwargs):
            kwargs["headers"] = self._merge_headers(kwargs.get("headers"))
            return self._client.get(url, **kwargs)
        
        def post(self, url, **kwargs):
            kwargs["headers"] = self._merge_headers(kwargs.get("headers"))
            return self._client.post(url, **kwargs)
        
        def put(self, url, **kwargs):
            kwargs["headers"] = self._merge_headers(kwargs.get("headers"))
            return self._client.put(url, **kwargs)
        
        def patch(self, url, **kwargs):
            kwargs["headers"] = self._merge_headers(kwargs.get("headers"))
            return self._client.patch(url, **kwargs)
        
        def delete(self, url, **kwargs):
            kwargs["headers"] = self._merge_headers(kwargs.get("headers"))
            return self._client.delete(url, **kwargs)
        
        def __getattr__(self, name):
            return getattr(self._client, name)
    
    with TestClient(app) as c:
        yield AuthenticatedClient(c, auth_headers)


@pytest.fixture(scope="function")
def sample_schedule(db_session, test_org, test_project):
    from datetime import date
    from app.models.schedule import ScheduleActivity
    activities = [
        ScheduleActivity(
            organization_id=test_org.id,
            project_id=test_project.id,
            activity_code="PIP-1023",
            activity_name="Erect Line 24-XX-101",
            discipline="Piping",
            wbs="PIP.10.23",
            planned_start=date(2026, 8, 15),
            planned_finish=date(2026, 8, 30),
        ),
        ScheduleActivity(
            organization_id=test_org.id,
            project_id=test_project.id,
            activity_code="PIP-1027",
            activity_name="Install Support for XX-101",
            discipline="Piping",
            wbs="PIP.10.27",
            planned_start=date(2026, 8, 10),
            planned_finish=date(2026, 8, 20),
        ),
        ScheduleActivity(
            organization_id=test_org.id,
            project_id=test_project.id,
            activity_code="PIP-1042",
            activity_name="Inspect XX-101",
            discipline="Piping",
            wbs="PIP.10.42",
            planned_start=date(2026, 9, 1),
            planned_finish=date(2026, 9, 5),
        ),
        ScheduleActivity(
            organization_id=test_org.id,
            project_id=test_project.id,
            activity_code="PIP-1050",
            activity_name="Hydrotest Line XX-101",
            discipline="Piping",
            wbs="PIP.10.50",
            planned_start=date(2026, 9, 5),
            planned_finish=date(2026, 9, 10),
        ),
        ScheduleActivity(
            organization_id=test_org.id,
            project_id=test_project.id,
            activity_code="MEC-2011",
            activity_name="Install Pump P-101",
            discipline="Mechanical",
            wbs="MEC.20.11",
            planned_start=date(2026, 8, 25),
            planned_finish=date(2026, 9, 5),
        ),
        ScheduleActivity(
            organization_id=test_org.id,
            project_id=test_project.id,
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
def sample_progress_excel_file():
    import io
    import pandas as pd
    from datetime import date
    df = pd.DataFrame([
        {"date": date(2026, 8, 30), "discipline": "Piping", "activity_description": "Started erection of XX-101 spool", "status": "Started", "equipment_tag": "XX-101", "location": "Area B", "reported_by": "Supervisor A"},
        {"date": date(2026, 8, 30), "discipline": "Civil", "activity_description": "Foundation A1 concrete pouring in progress", "status": "In Progress", "equipment_tag": "A1", "location": "Area C", "reported_by": "Supervisor B"},
        {"date": date(2026, 8, 29), "discipline": "Mechanical", "activity_description": "Pump P-101 installation completed", "status": "Completed", "equipment_tag": "P-101", "location": "Pump House", "reported_by": "Supervisor C"},
    ])
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return buffer