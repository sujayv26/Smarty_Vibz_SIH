from fastapi import FastAPI
from app.database import Base, engine
from app.api import schedule, progress, agent, matching
from app.models import schedule as schedule_model, progress as progress_model

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smarty Vibz API",
    description="Phase 1 & 2: Schedule ingestion, progress extraction, Time Agent, and Schedule Matching",
    version="2.0.0"
)

app.include_router(schedule.router)
app.include_router(progress.router)
app.include_router(agent.router)
app.include_router(matching.router)

@app.get("/")
async def root():
    return {"message": "Smarty Vibz API - Phase 1", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}