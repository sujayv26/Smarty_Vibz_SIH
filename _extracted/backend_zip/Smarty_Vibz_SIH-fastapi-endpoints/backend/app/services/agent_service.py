from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.models.progress import ProgressEvent
from app.schemas.progress import ProgressEventCreate
from app.schemas.agent import AgentChatRequest, AgentChatResponse, UnderstoodProgress, MatchedActivity
from app.services.extraction_service import get_extraction_provider

SESSION_CONTEXT = {}

def get_session_context(session_id: str) -> dict:
    if session_id not in SESSION_CONTEXT:
        SESSION_CONTEXT[session_id] = {"last_event_id": None, "events": []}
    return SESSION_CONTEXT[session_id]

def format_understood(understood: UnderstoodProgress) -> str:
    parts = []
    if understood.discipline:
        parts.append(understood.discipline)
    if understood.event_type:
        parts.append(understood.event_type)
    if understood.activity_reference:
        parts.append(understood.activity_reference)
    if understood.event_time:
        parts.append(f"at {understood.event_time}")
    if understood.event_date:
        parts.append(f"on {understood.event_date}")
    if understood.location:
        parts.append(f"in {understood.location}")
    return " — ".join(parts) if parts else "No details extracted"

def check_missing_fields(understood: UnderstoodProgress) -> list[str]:
    missing = []
    if not understood.activity_reference:
        missing.append("activity reference (what work was done)")
    # Only require activity_reference for now; discipline and location are optional
    return missing

def process_agent_chat(db: Session, request: AgentChatRequest) -> AgentChatResponse:
    session_id = request.session_id or "default"
    context = get_session_context(session_id)
    
    provider = get_extraction_provider()
    understood = provider.extract_agent_chat(request.message, context)
    
    message_lower = request.message.lower().strip()
    
    if "match" in message_lower and context["last_event_id"]:
        last_event = db.query(ProgressEvent).filter(ProgressEvent.id == context["last_event_id"]).first()
        if last_event:
            return AgentChatResponse(
                understood=UnderstoodProgress(),
                progress_event_id=context["last_event_id"],
                matched_activity=None,
                confidence=None,
                reply=f"Matching for event #{last_event.id} ({last_event.activity_reference or 'unknown'}) is not yet available. Phase 2 matching will be implemented later.",
                follow_up="You can log another progress report or wait for Phase 2."
            )
        else:
            return AgentChatResponse(
                understood=UnderstoodProgress(),
                progress_event_id=0,
                matched_activity=None,
                confidence=None,
                reply="No previous event found to match.",
                follow_up="Log a progress report first."
            )
    
    if "show me what i logged" in message_lower or "show me today" in message_lower:
        from datetime import date
        today = date.today()
        events = db.query(ProgressEvent).filter(
            ProgressEvent.event_date == today,
            ProgressEvent.session_id == session_id
        ).all()
        
        if not events:
            reply = "You haven't logged any progress events today."
        else:
            event_lines = [f"- #{e.id}: {e.activity_reference or 'N/A'} ({e.event_type}) at {e.event_time or 'N/A'} in {e.location or 'N/A'}" for e in events]
            reply = "Today's logged events:\n" + "\n".join(event_lines)
        
        return AgentChatResponse(
            understood=UnderstoodProgress(),
            progress_event_id=0,
            matched_activity=None,
            confidence=None,
            reply=reply,
            follow_up="Log another report or say 'match it' for the last event."
        )
    
    if "log another" in message_lower:
        return AgentChatResponse(
            understood=UnderstoodProgress(),
            progress_event_id=0,
            matched_activity=None,
            confidence=None,
            reply="Ready for a new progress report. What happened on site?",
            follow_up="Describe the work done (e.g., 'Started XX-101 spool erection at 9:30 AM in Area B')."
        )
    
    missing = check_missing_fields(understood)
    if missing and understood.event_type:
        missing_str = ", ".join(missing)
        reply = f"I understood: {format_understood(understood)}. However, I'm missing: {missing_str}. Could you provide these details?"
        follow_up = f"Please tell me: {missing_str}."
        return AgentChatResponse(
            understood=understood,
            progress_event_id=0,
            matched_activity=None,
            confidence=None,
            reply=reply,
            follow_up=follow_up
        )
    
    if not understood.event_type and not understood.activity_reference:
        return AgentChatResponse(
            understood=UnderstoodProgress(),
            progress_event_id=0,
            matched_activity=None,
            confidence=None,
            reply="I couldn't understand that. Please describe the work progress (e.g., 'Started piping work on XX-101 at 9 AM in Area B').",
            follow_up="Try saying what work started, progressed, or completed."
        )
    
    event_date = understood.event_date or date.today()
    
    progress_event = ProgressEventCreate(
        raw_text=request.message,
        activity_reference=understood.activity_reference,
        event_type=understood.event_type or "PROGRESS",
        event_date=event_date,
        event_time=understood.event_time,
        discipline=understood.discipline,
        location=understood.location,
        equipment_tag=understood.equipment_tag,
        source_type="AGENT_CHAT",
        source_file=None,
        session_id=session_id
    )
    
    db_event = ProgressEvent(**progress_event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    context["last_event_id"] = db_event.id
    context["events"].append(db_event.id)
    
    understood_str = format_understood(understood)
    reply = f"Got it. I've logged: {understood_str}."
    follow_up = "You can say 'match it' to find the schedule activity (Phase 2), or log another report."
    
    return AgentChatResponse(
        understood=understood,
        progress_event_id=db_event.id,
        matched_activity=None,
        confidence=None,
        reply=reply,
        follow_up=follow_up
    )

def get_session_events(db: Session, session_id: str) -> list[ProgressEvent]:
    return db.query(ProgressEvent).filter(
        ProgressEvent.session_id == session_id
    ).order_by(ProgressEvent.created_at).all()