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

def format_understood(understood: UnderstoodProgress, language: str = "en") -> str:
    if language == "hi":
        parts = []
        if understood.discipline:
            parts.append(understood.discipline)
        if understood.event_type:
            parts.append(understood.event_type)
        if understood.activity_reference:
            parts.append(understood.activity_reference)
        if understood.event_time:
            parts.append(f"{understood.event_time} baje")
        if understood.event_date:
            parts.append(f"{understood.event_date} ko")
        if understood.location:
            parts.append(f"{understood.location} mein")
        return " — ".join(parts) if parts else "Koi details nahi mile"
    elif language == "ta":
        parts = []
        if understood.discipline:
            parts.append(understood.discipline)
        if understood.event_type:
            parts.append(understood.event_type)
        if understood.activity_reference:
            parts.append(understood.activity_reference)
        if understood.event_time:
            parts.append(f"{understood.event_time} mani")
        if understood.event_date:
            parts.append(f"{understood.event_date} naal")
        if understood.location:
            parts.append(f"{understood.location} la")
        return " — ".join(parts) if parts else "Details kidaikkavillai"
    elif language == "te":
        parts = []
        if understood.discipline:
            parts.append(understood.discipline)
        if understood.event_type:
            parts.append(understood.event_type)
        if understood.activity_reference:
            parts.append(understood.activity_reference)
        if understood.event_time:
            parts.append(f"{understood.event_time} lo")
        if understood.event_date:
            parts.append(f"{understood.event_date} roju")
        if understood.location:
            parts.append(f"{understood.location} lo")
        return " — ".join(parts) if parts else "Details dorakaledu"
    elif language == "kn":
        parts = []
        if understood.discipline:
            parts.append(understood.discipline)
        if understood.event_type:
            parts.append(understood.event_type)
        if understood.activity_reference:
            parts.append(understood.activity_reference)
        if understood.event_time:
            parts.append(f"{understood.event_time} gante")
        if understood.event_date:
            parts.append(f"{understood.event_date} dina")
        if understood.location:
            parts.append(f"{understood.location} alli")
        return " — ".join(parts) if parts else "Details sigalilla"
    else:
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
    return missing

def get_localized_reply(key: str, language: str = "en", **kwargs) -> str:
    replies = {
        "match_not_available": {
            "en": "Matching for event #{event_id} ({activity_ref}) is not yet available. Phase 2 matching will be implemented later.",
            "hi": "Event #{event_id} ({activity_ref}) ke liye matching abhi available nahi hai. Phase 2 matching baad mein implement hoga.",
            "ta": "Event #{event_id} ({activity_ref}) ku matching ippo available illa. Phase 2 matching pinna implement aagum.",
            "te": "Event #{event_id} ({activity_ref}) kosam matching ippudu available ledu. Phase 2 matching tarvata implement avtundi.",
            "kn": "Event #{event_id} ({activity_ref}) ge matching ippattu available illa. Phase 2 matching nantara implement aaguttade.",
        },
        "no_previous_event": {
            "en": "No previous event found to match.",
            "hi": "Match karne ke liye koi pehle ka event nahi mila.",
            "ta": "Match panna mudiyavilla, munna event illai.",
            "te": "Match cheyadam kosam mundu event dorakaledu.",
            "kn": "Match maadakke hindina event sigalilla.",
        },
        "no_events_today": {
            "en": "You haven't logged any progress events today.",
            "hi": "Aaj aapne koi progress event log nahi kiya.",
            "ta": "Innum ungalukku inru progress event log pannavillai.",
            "te": "Meeru inku progress event log cheyakapoyaru.",
            "kn": "Neevu inru yavaga progress event log madidirilla.",
        },
        "ready_for_new": {
            "en": "Ready for a new progress report. What happened on site?",
            "hi": "Nayi progress report ke liye taiyaar. Site pe kya hua?",
            "ta": "Puthiya progress report ku thaiyar. Site la enna nadandhuchu?",
            "te": "Kotha progress report kosam thaiyaru. Site lo enti jarigindi?",
            "kn": "Hosa progress report ge thaiyaru. Site alli entu aayithu?",
        },
        "missing_fields": {
            "en": "I understood: {understood}. However, I'm missing: {missing}. Could you provide these details?",
            "hi": "Main samajh gaya: {understood}. Lekin yeh missing hai: {missing}. Kya aap yeh details de sakte hain?",
            "ta": "Naan purinthiruken: {understood}. Adhuve missing: {missing}. Ungalukku ithu tharalam?",
            "te": "Nenu ardam ayyindi: {understood}. Kani ivi missing: {missing}. Meeru ivi ivvachara?",
            "kn": "Nanu ardiruttene: {understood}. Adare ivi missing: {missing}. Neevu ivi kudiyabahara?",
        },
        "could_not_understand": {
            "en": "I couldn't understand that. Please describe the work progress (e.g., 'Started piping work on XX-101 at 9 AM in Area B').",
            "hi": "Main yeh samajh nahi paaya. Kripya kaam ka progress batayein (jaise, 'Piping work on XX-101 shuru kiya 9 baje Area B mein').",
            "ta": "Enakku puriyavillai. Velaip progress sollunga (uda: 'Piping work on XX-101 start pannirukku 9 mani Area B la').",
            "te": "Naku ardam ayyaledu. Panini progress cheppandi (uda: 'Piping work on XX-101 start chesaru 9 AM Area B lo').",
            "kn": "Nanage ardayitu. Kelasa progress heliri (uda: 'Piping work on XX-101 start madidaru 9 gante Area B alli').",
        },
        "logged_success": {
            "en": "Got it. I've logged: {understood}.",
            "hi": "Samajh gaya. Maine log kiya: {understood}.",
            "ta": "Purinthiruken. Naan log pannirukken: {understood}.",
            "te": "Ardam ayyindi. Nenu log chesaru: {understood}.",
            "kn": "Ardiruttene. Naanu log maadide: {understood}.",
        },
        "follow_up_match_or_log": {
            "en": "You can say 'match it' to find the schedule activity (Phase 2), or log another report.",
            "hi": "Aap 'match it' bol sakte hain schedule activity dhoondhne ke liye (Phase 2), ya dusri report log karein.",
            "ta": "Ungalukku 'match it' nu sollalam schedule activity thedikka (Phase 2), athava vera report log pannunga.",
            "te": "Meeru 'match it' ani cheppachu schedule activity tegedadam kosam (Phase 2), leda inkoka report log cheyyandi.",
            "kn": "Neenu 'match it' endare schedule activity thegedakke (Phase 2), athava vere report log maadi.",
        },
        "show_events_today": {
            "en": "Today's logged events:\n{events}",
            "hi": "Aaj ke logged events:\n{events}",
            "ta": "Inru log panna events:\n{events}",
            "te": "Inku log chesina events:\n{events}",
            "kn": "Inru log maadida events:\n{events}",
        },
    }
    lang_replies = replies.get(key, {})
    template = lang_replies.get(language, lang_replies.get("en", key))
    return template.format(**kwargs)

def process_agent_chat(db: Session, request: AgentChatRequest, preferred_language: str = "en", organization_id: int = None, user_id: int = None) -> AgentChatResponse:
    from app.models.project import Project
    
    session_id = request.session_id or "default"
    context = get_session_context(session_id)
    
    # Determine project_id from organization_id
    project_id = None
    if organization_id is not None:
        project = db.query(Project).filter(Project.organization_id == organization_id).first()
        if project:
            project_id = project.id
    
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
                reply=get_localized_reply("match_not_available", preferred_language, event_id=last_event.id, activity_ref=last_event.activity_reference or 'unknown'),
                follow_up=get_localized_reply("follow_up_match_or_log", preferred_language)
            )
        else:
            return AgentChatResponse(
                understood=UnderstoodProgress(),
                progress_event_id=0,
                matched_activity=None,
                confidence=None,
                reply=get_localized_reply("no_previous_event", preferred_language),
                follow_up=get_localized_reply("ready_for_new", preferred_language)
            )
    
    if "show me what i logged" in message_lower or "show me today" in message_lower:
        from datetime import date
        today = date.today()
        events = db.query(ProgressEvent).filter(
            ProgressEvent.event_date == today,
            ProgressEvent.session_id == session_id
        ).all()
        
        if not events:
            reply = get_localized_reply("no_events_today", preferred_language)
        else:
            if preferred_language == "hi":
                event_lines = [f"- #{e.id}: {e.activity_reference or 'N/A'} ({e.event_type}) {e.event_time or 'N/A'} baje {e.location or 'N/A'} mein" for e in events]
            elif preferred_language == "ta":
                event_lines = [f"- #{e.id}: {e.activity_reference or 'N/A'} ({e.event_type}) {e.event_time or 'N/A'} mani {e.location or 'N/A'} la" for e in events]
            elif preferred_language == "te":
                event_lines = [f"- #{e.id}: {e.activity_reference or 'N/A'} ({e.event_type}) {e.event_time or 'N/A'} lo {e.location or 'N/A'} lo" for e in events]
            elif preferred_language == "kn":
                event_lines = [f"- #{e.id}: {e.activity_reference or 'N/A'} ({e.event_type}) {e.event_time or 'N/A'} gante {e.location or 'N/A'} alli" for e in events]
            else:
                event_lines = [f"- #{e.id}: {e.activity_reference or 'N/A'} ({e.event_type}) at {e.event_time or 'N/A'} in {e.location or 'N/A'}" for e in events]
            reply = get_localized_reply("show_events_today", preferred_language, events="\n".join(event_lines))
        
        return AgentChatResponse(
            understood=UnderstoodProgress(),
            progress_event_id=0,
            matched_activity=None,
            confidence=None,
            reply=reply,
            follow_up=get_localized_reply("follow_up_match_or_log", preferred_language)
        )
    
    if "log another" in message_lower:
        return AgentChatResponse(
            understood=UnderstoodProgress(),
            progress_event_id=0,
            matched_activity=None,
            confidence=None,
            reply=get_localized_reply("ready_for_new", preferred_language),
            follow_up=get_localized_reply("ready_for_new", preferred_language)
        )
    
    missing = check_missing_fields(understood)
    if missing and understood.event_type:
        missing_str = ", ".join(missing)
        reply = get_localized_reply("missing_fields", preferred_language, understood=format_understood(understood, preferred_language), missing=missing_str)
        follow_up = get_localized_reply("missing_fields", preferred_language, understood=format_understood(understood, preferred_language), missing=missing_str)
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
            reply=get_localized_reply("could_not_understand", preferred_language),
            follow_up=get_localized_reply("could_not_understand", preferred_language)
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
    
    db_event = ProgressEvent(
        **progress_event.model_dump(),
        organization_id=organization_id,
        project_id=project_id,
        user_id=user_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    context["last_event_id"] = db_event.id
    context["events"].append(db_event.id)
    
    understood_str = format_understood(understood, preferred_language)
    reply = get_localized_reply("logged_success", preferred_language, understood=understood_str)
    follow_up = get_localized_reply("follow_up_match_or_log", preferred_language)
    
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