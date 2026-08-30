import json
import re
from datetime import date, datetime, timedelta
from typing import Optional
from app.services.extraction_provider import BaseExtractionProvider
from app.schemas.progress import ProgressEventCreate, EventType
from app.schemas.agent import UnderstoodProgress

class MockExtractionProvider(BaseExtractionProvider):
    def extract_progress(self, raw_text: str) -> ProgressEventCreate:
        text_lower = raw_text.lower()
        
        event_type = self._extract_event_type(text_lower)
        activity_reference = self._extract_activity_reference(raw_text)
        event_date = self._extract_date(raw_text)
        event_time = self._extract_time(raw_text)
        discipline = self._extract_discipline(text_lower)
        location = self._extract_location(raw_text)
        equipment_tag = self._extract_equipment_tag(raw_text)
        
        # Enhance activity reference with context
        if equipment_tag and activity_reference and equipment_tag not in activity_reference:
            activity_reference = f"{equipment_tag} {activity_reference}"
        elif equipment_tag and not activity_reference:
            activity_reference = equipment_tag

        return ProgressEventCreate(
            raw_text=raw_text,
            activity_reference=activity_reference,
            event_type=event_type,
            event_date=event_date,
            event_time=event_time,
            discipline=discipline,
            location=location,
            equipment_tag=equipment_tag,
            source_type="FREE_TEXT",
            source_file=None,
            session_id=None
        )

    def extract_agent_chat(self, message: str, context: Optional[dict] = None) -> UnderstoodProgress:
        text_lower = message.lower()
        
        if "match" in text_lower and context and context.get("last_event_id"):
            return UnderstoodProgress(
                activity_reference=None,
                event_type=None,
                event_date=None,
                event_time=None,
                discipline=None,
                location=None,
                equipment_tag=None
            )

        if "show me what i logged" in text_lower or "show me today" in text_lower:
            return UnderstoodProgress(
                activity_reference=None,
                event_type=None,
                event_date=None,
                event_time=None,
                discipline=None,
                location=None,
                equipment_tag=None
            )

        if "log another" in text_lower:
            return UnderstoodProgress(
                activity_reference=None,
                event_type=None,
                event_date=None,
                event_time=None,
                discipline=None,
                location=None,
                equipment_tag=None
            )

        event_type = self._extract_event_type(text_lower)
        activity_reference = self._extract_activity_reference(message)
        event_date = self._extract_date(message)
        event_time = self._extract_time(message)
        discipline = self._extract_discipline(text_lower)
        location = self._extract_location(message)
        equipment_tag = self._extract_equipment_tag(message)
        
        # For agent chat, default date to today if not specified
        if event_date is None:
            event_date = date.today()
        
        # Enhance activity reference with context
        if equipment_tag and activity_reference and equipment_tag not in activity_reference:
            activity_reference = f"{equipment_tag} {activity_reference}"
        elif equipment_tag and not activity_reference:
            activity_reference = equipment_tag

        return UnderstoodProgress(
            activity_reference=activity_reference,
            event_type=event_type,
            event_date=event_date,
            event_time=event_time,
            discipline=discipline,
            location=location,
            equipment_tag=equipment_tag
        )

    def _extract_event_type(self, text_lower: str) -> EventType:
        if any(kw in text_lower for kw in ["started", "start", "commenced", "begin"]):
            return "START"
        elif any(kw in text_lower for kw in ["progress", "in progress", "ongoing", "continuing"]):
            return "PROGRESS"
        elif any(kw in text_lower for kw in ["completed", "complete", "finished", "done"]):
            return "COMPLETE"
        elif any(kw in text_lower for kw in ["delayed", "delay", "late"]):
            return "DELAY"
        elif any(kw in text_lower for kw in ["hold", "on hold", "stopped", "pause"]):
            return "HOLD"
        return "PROGRESS"

    def _extract_activity_reference(self, text: str) -> Optional[str]:
        # First try to find descriptive activity patterns
        descriptive_patterns = [
            (r"erection.*spool|spool.*erection", "spool erection"),
            (r"piping\s+assembly", "piping assembly"),
            (r"pump\s+installation", "pump installation"),
            (r"cable\s+pulling", "cable pulling"),
            (r"foundation.*(?:concrete\s+)?pouring", "foundation concrete pouring"),
            (r"foundation\s+\w+", None),  # Keep as-is
        ]
        activity_desc = None
        for pattern, replacement in descriptive_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                activity_desc = replacement if replacement else match.group(1)
                break
        
        # Then try equipment/code patterns
        equipment_tag = None
        code_patterns = [
            r"(XX-\d+[-\w]*)",
            r"(PIP-\d+[-\w]*)",
            r"(MEC-\d+[-\w]*)",
            r"(CIV-\d+[-\w]*)",
            r"(ELE-\d+[-\w]*)",
            r"(P-\d+[-\w]*)",
        ]
        for pattern in code_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                equipment_tag = match.group(1)
                break
        
        # Combine equipment tag with activity description
        if equipment_tag and activity_desc:
            return f"{equipment_tag} {activity_desc}"
        elif equipment_tag:
            return equipment_tag
        elif activity_desc:
            return activity_desc
        return None

    def _extract_date(self, text: str) -> Optional[date]:
        today = date.today()
        if "today" in text.lower():
            return today
        if "yesterday" in text.lower():
            return today - timedelta(days=1)
        
        date_patterns = [
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{2}/\d{2}/\d{4})",
            r"(\d{2}-\d{2}-\d{4})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = match.group(1)
                    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"]:
                        try:
                            return datetime.strptime(date_str, fmt).date()
                        except ValueError:
                            continue
                except Exception:
                    continue
        return None

    def _extract_time(self, text: str) -> Optional[str]:
        time_patterns = [
            r"(\d{1,2}:\d{2}\s*[AP]M)",
            r"(\d{1,2}:\d{2})",
            r"(\d{1,2}\s*[AP]M)",
        ]
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                time_str = match.group(1).upper().replace(" ", "")
                if "AM" in time_str or "PM" in time_str:
                    try:
                        dt = datetime.strptime(time_str, "%I:%M%p")
                        return dt.strftime("%H:%M")
                    except ValueError:
                        try:
                            dt = datetime.strptime(time_str, "%I%p")
                            return dt.strftime("%H:%M")
                        except ValueError:
                            pass
                else:
                    try:
                        dt = datetime.strptime(time_str, "%H:%M")
                        return dt.strftime("%H:%M")
                    except ValueError:
                        pass
        return None

    def _extract_discipline(self, text_lower: str) -> Optional[str]:
        disciplines = ["piping", "civil", "mechanical", "electrical", "structural", "instrumentation"]
        for disc in disciplines:
            if disc in text_lower:
                return disc.capitalize()
        # Also check for "X team" patterns
        team_patterns = [
            (r"piping\s+team", "Piping"),
            (r"civil\s+team", "Civil"),
            (r"mechanical\s+team", "Mechanical"),
            (r"electrical\s+team", "Electrical"),
            (r"structural\s+team", "Structural"),
            (r"instrumentation\s+team", "Instrumentation"),
        ]
        for pattern, disc in team_patterns:
            if re.search(pattern, text_lower):
                return disc
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        location_patterns = [
            r"(area\s+[A-Z]\d?)",
            r"in\s+(area\s+[A-Z]\d?)",
            r"at\s+(area\s+[A-Z]\d?)",
            r"(pump house)",
            r"(substation)",
            r"(field)",
        ]
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Properly capitalize each word
                return ' '.join(word.capitalize() for word in match.group(1).split())
        return None

    def _extract_equipment_tag(self, text: str) -> Optional[str]:
        patterns = [
            r"(XX-\d+)",
            r"(P-\d+)",
            r"(SUB-\d+)",
            r"(A\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None