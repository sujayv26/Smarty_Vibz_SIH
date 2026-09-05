from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import settings

def _get_sync_url(url: str) -> str:
    return url.replace("postgresql+asyncpg", "postgresql+psycopg2").replace("postgresql://", "postgresql+psycopg2://")

def _get_async_url(url: str) -> str:
    if url.startswith("sqlite"):
        return url.replace("sqlite://", "sqlite+aiosqlite://")
    return url.replace("postgresql+psycopg2", "postgresql+asyncpg").replace("postgresql://", "postgresql+asyncpg://")

def _is_postgres(url: str) -> bool:
    return "postgresql" in url

sync_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
async_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

# Sync engine for Alembic and Celery tasks
if _is_postgres(settings.DATABASE_URL):
    sync_engine = create_engine(
        _get_sync_url(settings.DATABASE_URL),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args=sync_connect_args,
    )
else:
    sync_engine = create_engine(
        _get_sync_url(settings.DATABASE_URL),
        poolclass=NullPool,
        connect_args=sync_connect_args,
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Async engine for FastAPI
if _is_postgres(settings.DATABASE_URL):
    async_engine = create_async_engine(
        _get_async_url(settings.DATABASE_URL),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args=async_connect_args,
    )
else:
    async_engine = create_async_engine(
        _get_async_url(settings.DATABASE_URL),
        poolclass=NullPool,
        connect_args=async_connect_args,
    )
AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session