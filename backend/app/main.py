from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, sync_engine
from app.api import schedule, progress, agent, matching, confidence, reviews, audit, xer_import, xer_export, auth, webhooks
from app.models import schedule as schedule_model, progress as progress_model, confidence as confidence_model, xer as xer_model
from app.models import organization, user, project, ingestion_source, wbs_node, event_wbs_match, glossary_mapping, delay_reason, productivity_benchmark, audit_log
from app.core.config import settings

Base.metadata.create_all(bind=sync_engine)

app = FastAPI(
    title="Smarty Vibz API",
    description="Phase 1, 2, 3 & 4: Schedule ingestion, progress extraction, Time Agent, Schedule Matching, Confidence & Review, P6/XER Interoperability",
    version="4.0.0"
)

cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*", "X-CSRF-Token"],
    expose_headers=["*"],
)

app.include_router(auth.router)
app.include_router(schedule.router)
app.include_router(progress.router)
app.include_router(agent.router)
app.include_router(matching.router)
app.include_router(confidence.router)
app.include_router(reviews.router)
app.include_router(audit.router)
app.include_router(xer_import.router)
app.include_router(xer_export.router)
app.include_router(webhooks.router)

@app.get("/")
async def root():
    return {"message": "Smarty Vibz API - Phase 3", "version": "3.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}