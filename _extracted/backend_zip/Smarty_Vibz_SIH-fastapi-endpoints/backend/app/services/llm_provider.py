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
Extract structured progress information from this field report:
"{raw_text}"

Return JSON with these fields (use null for missing information):
- activity_reference: Work reference/identifier mentioned
- event_type: One of START, PROGRESS, COMPLETE, DELAY, HOLD
- event_date: Date in YYYY-MM-DD format or null
- event_time: Time in HH:MM format or null
- discipline: Discipline (Piping, Civil, Mechanical, Electrical, etc.) or null
- location: Site location/area or null
- equipment_tag: Equipment/tag identifier or null

Do not hallucinate. Only extract what is explicitly in the text.
"""

    def _build_agent_prompt(self, message: str, context: Optional[dict]) -> str:
        ctx = ""
        if context and context.get("last_event"):
            ctx = f"Previous event: {context['last_event']}\n"
        return f"""
{ctx}
User message: "{message}"

Extract structured progress information. Return JSON with:
- activity_reference: Work reference/identifier or null
- event_type: START, PROGRESS, COMPLETE, DELAY, HOLD, or null
- event_date: YYYY-MM-DD or null
- event_time: HH:MM or null
- discipline: Discipline or null
- location: Location or null
- equipment_tag: Equipment tag or null

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