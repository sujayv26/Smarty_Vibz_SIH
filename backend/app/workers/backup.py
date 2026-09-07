import os
import shutil
from datetime import datetime
from celery import shared_task
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

BACKUP_DIR = os.getenv("BACKUP_DIR", "/app/backups")
RETENTION_COUNT = 24


# Type mapping from SQLAlchemy/Postgres types to SQLite types
TYPE_MAPPING = {
    "INTEGER": "INTEGER",
    "BIGINT": "INTEGER",
    "SMALLINT": "INTEGER",
    "VARCHAR": "TEXT",
    "TEXT": "TEXT",
    "CHAR": "TEXT",
    "BOOLEAN": "INTEGER",  # SQLite uses 0/1 for boolean
    "DATE": "DATE",
    "TIMESTAMP": "DATETIME",
    "DATETIME": "DATETIME",
    "TIME": "TIME",
    "FLOAT": "REAL",
    "DOUBLE PRECISION": "REAL",
    "NUMERIC": "REAL",
    "UUID": "TEXT",
    "JSON": "TEXT",
    "JSONB": "TEXT",
    "ARRAY": "TEXT",
    "ENUM": "TEXT",
}


def _get_column_type(engine, table_name, column_name):
    """Get the actual column type from the source database."""
    insp = inspect(engine)
    columns = insp.get_columns(table_name)
    for col in columns:
        if col["name"] == column_name:
            return str(col["type"]).upper()
    return "TEXT"


def _map_to_sqlite_type(pg_type: str) -> str:
    """Map PostgreSQL/SQLAlchemy type to SQLite type."""
    pg_type = pg_type.upper()
    # Handle parameterized types like VARCHAR(255), NUMERIC(10,2)
    base_type = pg_type.split("(")[0]
    return TYPE_MAPPING.get(base_type, "TEXT")


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

        sqlite_engine = create_engine(f"sqlite:///{backup_path}")

        for table in tables:
            result = db.execute(text(f"SELECT * FROM {table}"))
            rows = result.fetchall()
            if rows:
                columns = list(result.keys())
                # Get actual column types from source
                col_types = []
                for col in columns:
                    pg_type = _get_column_type(engine, table, col)
                    sqlite_type = _map_to_sqlite_type(pg_type)
                    col_types.append(f"{col} {sqlite_type}")

                create_sql = f"CREATE TABLE {table} (" + ", ".join(col_types) + ")"

                with sqlite_engine.connect() as sqlite_conn:
                    sqlite_conn.execute(text(create_sql))
                    for row in rows:
                        # Use named parameters (p0, p1, ...) for SQLAlchemy 2.0 compatibility with SQLite
                        placeholders = ", ".join([f":p{i}" for i in range(len(columns))])
                        insert_sql = f"INSERT INTO {table} VALUES ({placeholders})"
                        # Convert row to dict with named parameters, handling boolean conversion
                        row_params = {}
                        for i, col in enumerate(columns):
                            val = row[i]
                            pg_type = _get_column_type(engine, table, col).upper()
                            if "BOOL" in pg_type and val is not None:
                                # Convert boolean to 0/1 for SQLite
                                row_params[f"p{i}"] = 1 if val else 0
                            else:
                                row_params[f"p{i}"] = val
                        sqlite_conn.execute(text(insert_sql), row_params)
                    sqlite_conn.commit()

        cleanup_old_backups()
        return {"status": "success", "backup_file": backup_filename}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
        sqlite_engine.dispose()


def cleanup_old_backups():
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith("consight_backup_") and f.endswith(".db")])
    while len(backups) > RETENTION_COUNT:
        oldest = backups.pop(0)
        os.remove(os.path.join(BACKUP_DIR, oldest))