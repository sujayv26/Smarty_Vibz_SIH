from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.agent_service import process_agent_chat, get_session_events
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.schemas.progress import ProgressEventResponse

router = APIRouter(prefix="/agent", tags=["Time Agent"])

@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest, db: Session = Depends(get_db)):
    try:
        response = process_agent_chat(db, request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@router.get("/sessions/{session_id}/events", response_model=list[ProgressEventResponse])
async def get_session_events_endpoint(session_id: str, db: Session = Depends(get_db)):
    events = get_session_events(db, session_id)
    return events