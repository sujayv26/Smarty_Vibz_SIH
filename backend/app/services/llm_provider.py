from app.services.extraction_provider import BaseExtractionProvider
from app.schemas.progress import ProgressEventCreate, SourceType, EventType
from app.schemas.agent import UnderstoodProgress
from typing import Optional
import json


class LLMExtractionProvider(BaseExtractionProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def extract_progress(self, raw_text: str) -> ProgressEventCreate:
        prompt = self._build_progress_prompt(raw_text)
        response = self._call_llm(prompt)
        return self._parse_progress_response(response, raw_text)

    def extract_agent_chat(self, message: str, context: Optional[dict] = None) -> UnderstoodProgress:
        prompt = self._build_agent_prompt(message, context)
        response = self._call_llm(prompt)
        return self._parse_agent_response(response)

    def _build_progress_prompt(self, raw_text: str) -> str:
        return f"""
You are an expert construction progress extraction system. Extract structured progress information from this field report, which may be in English, Hindi-English, Tamil-English, Telugu-English, or other code-mixed languages.

Field report: "{raw_text}"

Return JSON with these fields (use null for missing information):
- activity_reference: Work reference/identifier mentioned (preserve activity codes like XX-101, PIP-1023, P-101 exactly as written)
- event_type: One of START, PROGRESS, COMPLETE, DELAY, HOLD
- event_date: Date in YYYY-MM-DD format or null
- event_time: Time in HH:MM format (24-hour) or null
- discipline: Discipline (Piping, Civil, Mechanical, Electrical, Structural, Instrumentation, HVAC, Fire Protection) or null
- location: Site location/area or null
- equipment_tag: Equipment/tag identifier or null

Key multilingual extraction rules:
- Preserve activity codes (XX-101, PIP-1023, MEC-2011, etc.) and technical terms exactly as written
- Hindi-English: "shuru kiya" = START, "chal raha" = PROGRESS, "complete ho gaya" = COMPLETE, "delay" = DELAY, "hold" = HOLD
- Tamil-English: "start pannirukku" = START, "seiyum" = PROGRESS, "mudichiruku" = COMPLETE, "delay aagiruku" = DELAY
- Telugu-English: "start chesaru" = START, "chestunaru" = PROGRESS, "ayyindi" = COMPLETE, "delay ayyindi" = DELAY
- Kannada-English: "start madidaru" = START, "maadutiddare" = PROGRESS, "aayithu" = COMPLETE, "delay aayithu" = DELAY, "hold aayithu" = HOLD
- Time formats: "9:30 baje", "8:00 mani", "11:00" all map to HH:MM 24-hour format
- Date keywords: "aaj"/"today" = today, "kal"/"naalai"/"repu"/"nale" = tomorrow, "parson"/"naalai kaalai" = day after tomorrow
- Location patterns: "Area B mein", "Area D la", "Area F lo", "Area L alli" all indicate location
- Discipline inference: "piping team" = Piping, "civil team" = Civil, "mechanical team" = Mechanical, etc.

Do not hallucinate. Only extract what is explicitly in the text.
"""

    def _build_agent_prompt(self, message: str, context: Optional[dict]) -> str:
        ctx = ""
        if context and context.get("last_event"):
            ctx = f"Previous event: {context['last_event']}\n"
        return f"""
{ctx}
User message: "{message}"

Extract structured progress information. The user may write in English, Hindi-English, Tamil-English, Telugu-English, or other code-mixed languages. Return JSON with:
- activity_reference: Work reference/identifier or null (preserve codes like XX-101, PIP-1023 exactly)
- event_type: START, PROGRESS, COMPLETE, DELAY, HOLD, or null
- event_date: YYYY-MM-DD or null
- event_time: HH:MM or null
- discipline: Discipline or null
- location: Location or null
- equipment_tag: Equipment tag or null

Multilingual understanding:
- Hindi-English: "shuru kiya", "chal raha", "complete ho gaya", "delay", "hold"
- Tamil-English: "start pannirukku", "seiyum", "mudichiruku", "delay aagiruku"
- Telugu-English: "start chesaru", "chestunaru", "ayyindi", "delay ayyindi"
- Kannada-English: "start madidaru", "maadutiddare", "aayithu", "delay aayithu", "hold aayithu"
- Time: "9:30 baje", "8:00 mani", "11:00" -> HH:MM format
- Location: "mein", "la", "lo", "alli" indicate location

If user says "match it", return all nulls.
If user asks to show logged events, return all nulls.
If user says "log another", return all nulls.
Do not hallucinate missing fields.
"""

    def _call_llm(self, prompt: str) -> str:
        raise NotImplementedError("LLM provider not implemented - use mock provider for testing")

    def _parse_progress_response(self, response: str, raw_text: str) -> ProgressEventCreate:
        data = json.loads(response)
        return ProgressEventCreate(
            raw_text=raw_text,
            activity_reference=data.get("activity_reference"),
            event_type=data.get("event_type", "PROGRESS"),
            event_date=data.get("event_date"),
            event_time=data.get("event_time"),
            discipline=data.get("discipline"),
            location=data.get("location"),
            equipment_tag=data.get("equipment_tag"),
            source_type=SourceType.FREE_TEXT,
            source_file=None,
            session_id=None
        )

    def _parse_agent_response(self, response: str) -> UnderstoodProgress:
        data = json.loads(response)
        return UnderstoodProgress(
            activity_reference=data.get("activity_reference"),
            event_type=data.get("event_type"),
            event_date=data.get("event_date"),
            event_time=data.get("event_time"),
            discipline=data.get("discipline"),
            location=data.get("location"),
            equipment_tag=data.get("equipment_tag")
        )