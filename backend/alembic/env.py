from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import schedule, progress, confidence, xer
from app.models.organization import Organization
from app.models.user import User
from app.models.project import Project
from app.models.ingestion_source import IngestionSource
from app.models.wbs_node import WBSNode
from app.models.event_wbs_match import EventWBSMatch
from app.models.glossary_mapping import GlossaryMapping
from app.models.delay_reason import DelayReason
from app.models.productivity_benchmark import ProductivityBenchmark
from app.models.audit_log import AuditLog

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    from app.core.config import settings
    return settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()