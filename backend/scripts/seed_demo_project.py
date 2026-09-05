#!/usr/bin/env python3
"""Seed demo organization, project, and users for testing."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.ingestion_source import IngestionSource
from app.core.security import get_password_hash


def seed():
    db: Session = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.slug == "demo").first()
        if not org:
            org = Organization(
                name="Demo Construction Co.",
                slug="demo",
                description="Demo organization for testing",
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"Created organization: {org.name} (id={org.id})")
        else:
            print(f"Organization exists: {org.name} (id={org.id})")

        sources = [
            ("VOICE", "Voice/Time-Agent", "Supervisor voice notes via Time-Agent"),
            ("TIME_AGENT", "Time-Agent Chat", "Conversational Time-Agent chat"),
            ("TEXT_DIARY", "Text Diary", "Manual text diary entries"),
            ("SPREADSHEET", "Spreadsheet Upload", "Excel/CSV progress uploads"),
            ("PDF_OCR", "PDF/OCR Scan", "Scanned daily diaries via OCR"),
            ("PMIS_EXPORT", "PMIS Export", "Automated PMIS schedule exports"),
            ("WHATSAPP", "WhatsApp", "WhatsApp Business Cloud API messages"),
        ]
        for code, name, desc in sources:
            src = db.query(IngestionSource).filter(IngestionSource.code == code).first()
            if not src:
                src = IngestionSource(code=code, name=name, description=desc)
                db.add(src)
        db.commit()
        print("Seeded ingestion sources")

        users = [
            ("admin@demo.com", "admin123", "System Admin", UserRole.SYSTEM_ADMIN, None, "en"),
            ("contractor@demo.com", "contractor123", "Contractor Admin", UserRole.CONTRACTOR_ADMIN, org.id, "en"),
            ("controls@demo.com", "controls123", "Project Controls", UserRole.PROJECT_CONTROLS, org.id, "en"),
            ("planner@demo.com", "planner123", "Discipline Planner", UserRole.DISCIPLINE_PLANNER, org.id, "en"),
            ("supervisor@demo.com", "supervisor123", "Site Supervisor", UserRole.SITE_SUPERVISOR, org.id, "en"),
        ]
        for email, pwd, name, role, org_id, lang in users:
            u = db.query(User).filter(User.email == email).first()
            if not u:
                u = User(
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    full_name=name,
                    role=role,
                    organization_id=org_id or org.id,
                    discipline="Civil" if role == UserRole.DISCIPLINE_PLANNER else None,
                    preferred_language=lang,
                )
                db.add(u)
                print(f"Created user: {email} ({role.value})")
            else:
                print(f"User exists: {email}")
        db.commit()

        project = db.query(Project).filter(Project.code == "DEMO-001").first()
        if not project:
            project = Project(
                name="Demo Highway Project",
                code="DEMO-001",
                description="Demo project for testing",
                organization_id=org.id,
                location="Demo City, Demo State",
                latitude="12.3456",
                longitude="78.9012",
            )
            db.add(project)
            db.commit()
            print(f"Created project: {project.name} (id={project.id})")
        else:
            print(f"Project exists: {project.name} (id={project.id})")

        print("\n=== Demo Credentials ===")
        print("admin@demo.com / admin123 (System Admin)")
        print("contractor@demo.com / contractor123 (Contractor Admin)")
        print("controls@demo.com / controls123 (Project Controls)")
        print("planner@demo.com / planner123 (Discipline Planner)")
        print("supervisor@demo.com / supervisor123 (Site Supervisor)")

    finally:
        db.close()


if __name__ == "__main__":
    seed()