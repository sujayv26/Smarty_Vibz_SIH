from fastapi import FastAPI
from app.database import Base, engine
from app.api import schedule, progress, agent, matching, confidence, reviews, audit, xer_import, xer_export
from app.models import schedule as schedule_model, progress as progress_model, confidence as confidence_model, xer as xer_model

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smarty Vibz API",
    description="Phase 1, 2, 3 & 4: Schedule ingestion, progress extraction, Time Agent, Schedule Matching, Confidence & Review, P6/XER Interoperability",
    version="4.0.0"
)

app.include_router(schedule.router)
app.include_router(progress.router)
app.include_router(agent.router)
app.include_router(matching.router)
app.include_router(confidence.router)
app.include_router(reviews.router)
app.include_router(audit.router)
app.include_router(xer_import.router)
app.include_router(xer_export.router)

@app.get("/")
async def root():
    return {"message": "Smarty Vibz API - Phase 3", "version": "3.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}