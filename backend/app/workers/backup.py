import os
import shutil
from datetime import datetime
from celery import shared_task
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

BACKUP_DIR = "/app/backups"
RETENTION_COUNT = 24


@shared_task(name="app.workers.backup.backup_to_sqlite")
def backup_to_sqlite():
    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"consight_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")
    engine = create_engine(sync_url)
    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()
    try:
        tables = [
            "organizations",
            "users",
            "projects",
            "ingestion_sources",
            "wbs_nodes",
            "schedule_activities",
            "progress_events",
            "confidence_results",
            "planner_reviews",
            "audit_records",
            "external_schedules",
            "schedule_relationships",
            "event_wbs_matches",
            "glossary_mappings",
            "delay_reasons",
            "productivity_benchmarks",
            "audit_logs",
        ]

        for table in tables:
            result = db.execute(text(f"SELECT * FROM {table}"))
            rows = result.fetchall()
            if rows:
                columns = result.keys()
                create_sql = f"CREATE TABLE {table} ("
                col_defs = []
                for col in columns:
                    col_defs.append(f"{col} TEXT")
                create_sql += ", ".join(col_defs) + ")"

                sqlite_engine = create_engine(f"sqlite:///{backup_path}")
                with sqlite_engine.connect() as sqlite_conn:
                    sqlite_conn.execute(text(create_sql))
                    for row in rows:
                        placeholders = ", ".join(["?" for _ in columns])
                        insert_sql = f"INSERT INTO {table} VALUES ({placeholders})"
                        sqlite_conn.execute(text(insert_sql), row)
                    sqlite_conn.commit()

        cleanup_old_backups()
        return {"status": "success", "backup_file": backup_filename}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


def cleanup_old_backups():
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith("consight_backup_") and f.endswith(".db")])
    while len(backups) > RETENTION_COUNT:
        oldest = backups.pop(0)
        os.remove(os.path.join(BACKUP_DIR, oldest))