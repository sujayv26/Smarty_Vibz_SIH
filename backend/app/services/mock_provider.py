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
        
        # If text indicates ongoing work (present continuous), keep as PROGRESS even if date is future
        ongoing_keywords = [
            "kar rahe hain", "chal raha", "chalu", "jaari",  # Hindi
            "seiyum", "seyrirukku",  # Tamil
            "chestunaru", "chestundi",  # Telugu
            "maadutiddare", "maadutidda", "chalu",  # Kannada
        ]
        is_ongoing = any(kw in text_lower for kw in ongoing_keywords)
        
        # If event is scheduled for tomorrow/future and type is PROGRESS (and not ongoing), change to START
        today = date.today()
        if event_date and event_date > today and event_type == "PROGRESS" and not is_ongoing:
            event_type = "START"
        
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
        # English keywords
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
        
        # Hindi-English code-mixed keywords
        if any(kw in text_lower for kw in ["shuru", "start kiya", "shuru kiya", "aarambh"]):
            return "START"
        elif any(kw in text_lower for kw in ["chal raha", "chalu", "progress", "jaari"]):
            return "PROGRESS"
        elif any(kw in text_lower for kw in ["complete ho gaya", "finished", "khatam", "poora", "mudichiruku", "ayyindi"]):
            return "COMPLETE"
        elif any(kw in text_lower for kw in ["delay", "late", "deri", "delay aagiruku", "delay ayyindi"]):
            return "DELAY"
        elif any(kw in text_lower for kw in ["hold", "pause", "roka", "hold pe", "hold ayyindi"]):
            return "HOLD"
        
        # Tamil-English code-mixed keywords
        if any(kw in text_lower for kw in ["start pannirukku", "start pannum", "aarambithu"]):
            return "START"
        elif any(kw in text_lower for kw in ["seiyum", "seyrirukku", "progress"]):
            return "PROGRESS"
        elif any(kw in text_lower for kw in ["mudichiruku", "mudichu", "complete aachu"]):
            return "COMPLETE"
        elif any(kw in text_lower for kw in ["delay aagiruku", "delay aagum"]):
            return "DELAY"
        elif any(kw in text_lower for kw in ["hold", "niyamithu"]):
            return "HOLD"
        
        # Telugu-English code-mixed keywords
        if any(kw in text_lower for kw in ["start chesaru", "start chesam", "aarambhicharu"]):
            return "START"
        elif any(kw in text_lower for kw in ["chestunaru", "chestundi", "progress"]):
            return "PROGRESS"
        elif any(kw in text_lower for kw in ["ayyindi", "mudichindi", "complete ayyindi"]):
            return "COMPLETE"
        elif any(kw in text_lower for kw in ["delay ayyindi", "delay ayyum"]):
            return "DELAY"
        elif any(kw in text_lower for kw in ["hold ayyindi", "hold chesaru"]):
            return "HOLD"
        
        # Kannada-English code-mixed keywords
        if any(kw in text_lower for kw in ["start madidaru", "start madidaru", "aarambha"]):
            return "START"
        elif any(kw in text_lower for kw in ["maadutiddare", "maadutidda", "progress", "chalu"]):
            return "PROGRESS"
        elif any(kw in text_lower for kw in ["aayithu", "mudiyithu", "complete aayithu"]):
            return "COMPLETE"
        elif any(kw in text_lower for kw in ["delay aayithu", "delay aagutte"]):
            return "DELAY"
        elif any(kw in text_lower for kw in ["hold aayithu", "hold maadidaru"]):
            return "HOLD"
        
        return "PROGRESS"

    def _extract_activity_reference(self, text: str) -> Optional[str]:
        # First try to find descriptive activity patterns (English + code-mixed)
        descriptive_patterns = [
            # More specific patterns first
            (r"hvac\s+duct\s+installation", "HVAC duct installation"),
            (r"fire\s+protection\s+pipe\s+installation", "fire protection pipe installation"),
            (r"fire\s+protection\s+sprinkler\s+installation", "sprinkler installation"),
            (r"sprinkler\s+installation", "sprinkler installation"),
            (r"cooling\s+tower\s+piping\s+erection", "cooling tower piping erection"),
            (r"cooling\s+tower\s+piping", "cooling tower piping"),
            (r"control\s+panel\s+installation", "control panel installation"),
            (r"control\s+room\s+cable\s+pulling", "control room cable pulling"),
            (r"transformer\s+installation", "transformer installation"),
            (r"instrumentation\s+cable\s+tray", "instrumentation cable tray"),
            (r"cable\s+tray\s+erection", "cable tray erection"),
            (r"cable\s+termination", "cable termination"),
            (r"cable\s+pulling", "cable pulling"),
            (r"flange\s+bolt\s+up", "flange bolt up"),
            (r"valve\s+installation", "valve installation"),
            (r"pump\s+(?:P-\d+\s+)?installation", "pump installation"),
            (r"beam\s+erection", "beam erection"),
            (r"piping\s+erection", "piping erection"),
            (r"erection.*spool|spool.*erection", "spool erection"),
            (r"spool\s+fabrication", "spool fabrication"),
            (r"spool\s+welding|welding.*spool", "spool welding"),
            (r"spool\s+hydrotest", "spool hydrotest"),
            (r"piping\s+assembly", "piping assembly"),
            (r"fabrication", "fabrication"),
            (r"welding", "welding"),
            (r"hydrotest", "hydrotest"),
            (r"foundation\s+\w+\s+concrete\s+pouring", "foundation concrete pouring"),
            (r"foundation\s+\w+\s+concrete\s+pour", "foundation concrete pouring"),
            (r"concrete\s+pouring", "concrete pouring"),
            (r"concrete\s+pour", "concrete pouring"),
            (r"foundation\s+\w+", "foundation"),
            (r"duct\s+installation", "duct installation"),
        ]
        activity_desc = None
        foundation_code = None
        # Extract foundation code first if present
        foundation_match = re.search(r"foundation\s+(\w+)", text, re.IGNORECASE)
        if foundation_match:
            foundation_code = foundation_match.group(1).upper()
        
        for pattern, replacement in descriptive_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                activity_desc = replacement
                # For foundation patterns, include the foundation code
                if "foundation" in replacement and foundation_code:
                    activity_desc = f"foundation {foundation_code} {replacement.replace('foundation', '').strip()}"
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
            r"(SUB-\d+[-\w]*)",
            r"(A\d+)",
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
        text_lower = text.lower()
        
        # English
        if "today" in text_lower or "aaj" in text_lower:
            return today
        if "yesterday" in text_lower:
            return today - timedelta(days=1)
        if "tomorrow" in text_lower or "kal" in text_lower or "naalai" in text_lower or "repu" in text_lower or "nale" in text_lower:
            return today + timedelta(days=1)
        
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
            # Hindi patterns like "9:30 baje", "10 baje"
            r"(\d{1,2}:\d{2}\s*baje)",
            r"(\d{1,2}\s*baje)",
            # Tamil patterns like "8:00 mani", "7:00 mani"
            r"(\d{1,2}:\d{2}\s*mani)",
            r"(\d{1,2}\s*mani)",
            # Kannada patterns like "9:00 AM", "10:30"
            # Telugu patterns like "11:00", "6:00"
        ]
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                time_str = match.group(1).upper().replace(" ", "")
                # Clean up Hindi/Tamil/Telugu suffixes
                time_str = time_str.replace("BAJE", "").replace("MANI", "")
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
                        # Try just hour
                        try:
                            dt = datetime.strptime(time_str, "%H")
                            return dt.strftime("%H:%M")
                        except ValueError:
                            pass
        return None

    def _extract_discipline(self, text_lower: str) -> Optional[str]:
        # English disciplines
        disciplines = ["piping", "civil", "mechanical", "electrical", "structural", "instrumentation", "hvac", "fire protection"]
        for disc in disciplines:
            if disc in text_lower:
                # Map fire protection to Mechanical
                if disc == "fire protection":
                    return "Mechanical"
                return disc.capitalize() if disc != "hvac" else "Mechanical"
        
        # Also check for "X team" patterns (English)
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
        
        # Hindi-English team patterns
        hi_patterns = [
            (r"piping\s+team", "Piping"),
            (r"civil\s+team", "Civil"),
            (r"mechanical\s+team", "Mechanical"),
            (r"electrical\s+team", "Electrical"),
        ]
        for pattern, disc in hi_patterns:
            if re.search(pattern, text_lower):
                return disc
        
        # Infer discipline from equipment tags and activity keywords
        # Mechanical: P-*, MEC-*, pump, valve, cooling tower, fire protection, sprinkler, HVAC, duct
        if re.search(r"\b(P-\d+|MEC-\d+|pump|valve|cooling\s+tower|fire\s+protection|sprinkler|hvac|duct)\b", text_lower):
            return "Mechanical"
        
        # Piping: XX-*, PIP-*, spool, hydrotest, flange, pipe
        if re.search(r"\b(XX-\d+|PIP-\d+|spool|hydrotest|flange|pipe\s+erection|pipe\s+installation)\b", text_lower):
            return "Piping"
        
        # Electrical: ELE-*, SUB-*, cable, transformer, control panel, substation, termination, tray
        if re.search(r"\b(ELE-\d+|SUB-\d+|cable|transformer|control\s+panel|substation|termination|cable\s+tray)\b", text_lower):
            return "Electrical"
        
        # Civil: CIV-*, foundation, concrete, pouring
        if re.search(r"\b(CIV-\d+|foundation|concrete\s+pouring|concrete\s+pour)\b", text_lower):
            return "Civil"
        
        # Structural: beam, structural
        if re.search(r"\b(beam|structural)\b", text_lower):
            return "Structural"
        
        # Instrumentation: instrumentation
        if re.search(r"\binstrumentation\b", text_lower):
            return "Instrumentation"
        
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        location_patterns = [
            r"(area\s+[A-Z]\d?)",
            r"in\s+(area\s+[A-Z]\d?)",
            r"at\s+(area\s+[A-Z]\d?)",
            r"(pump house)",
            r"(substation)",
            r"(field)",
            r"(plant room)",
            r"(control room)",
            # Foundation areas - convert "foundation X" to "Area X" (only alphanumeric codes)
            r"foundation\s+([A-Z]\d+)",
            # Hindi patterns
            r"in\s+(area\s+[A-Z]\d?)",
            r"mein\s+(area\s+[A-Z]\d?)",
            r"(area\s+[A-Z]\d?)\s+mein",
            # Tamil patterns
            r"(area\s+[A-Z]\d?)\s+la",
            r"la\s+(area\s+[A-Z]\d?)",
            # Telugu patterns
            r"(area\s+[A-Z]\d?)\s+lo",
            r"lo\s+(area\s+[A-Z]\d?)",
            # Kannada patterns
            r"(area\s+[A-Z]\d?)\s+alli",
            r"alli\s+(area\s+[A-Z]\d?)",
        ]
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1)
                # Convert "foundation X" to "Area X" (pattern captures just the code)
                if pattern.startswith("foundation"):
                    return f"Area {location.upper()}"
                # Properly capitalize each word
                return ' '.join(word.capitalize() for word in location.split())
        return None

    def _extract_equipment_tag(self, text: str) -> Optional[str]:
        patterns = [
            r"(XX-\d+[-\w]*)",
            r"(PIP-\d+[-\w]*)",
            r"(MEC-\d+[-\w]*)",
            r"(CIV-\d+[-\w]*)",
            r"(ELE-\d+[-\w]*)",
            r"(P-\d+[-\w]*)",
            r"(SUB-\d+[-\w]*)",
            # A\d+ but not if it's "foundation A1", "area A1" etc.
            r"(?<!foundation\s)(?<!area\s)(A\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None