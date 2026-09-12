import re
from typing import Optional
from app.models.progress import ProgressEvent
from app.models.schedule import ScheduleActivity


def extract_identifiers(text: str) -> list[str]:
    if not text:
        return []
    
    patterns = [
        r"\b([A-Z]{2,4}-\d{3,4}[-\w]*)\b",
        r"\b(XX-\d+[-\w]*)\b",
        r"\b(P-\d+[-\w]*)\b",
        r"\b(SUB-\d+[-\w]*)\b",
        r"\b(MCC-\d+[-\w]*)\b",
    ]
    
    identifiers = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        identifiers.extend([m.upper() for m in matches])
    
    return list(set(identifiers))


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"[^a-zA-Z0-9]+", " ", text.lower()).strip()


def exact_match_score(event: ProgressEvent, activity: ScheduleActivity) -> tuple[float, list[str]]:
    reasons = []
    score = 0.0
    
    event_identifiers = extract_identifiers(event.raw_text)
    if event.activity_reference:
        event_identifiers.extend(extract_identifiers(event.activity_reference))
    if event.equipment_tag:
        event_identifiers.append(event.equipment_tag.upper())
    
    activity_identifiers = extract_identifiers(activity.activity_code)
    activity_identifiers.extend(extract_identifiers(activity.activity_name))
    
    event_ids_normalized = set(normalize_text(id_) for id_ in event_identifiers)
    activity_ids_normalized = set(normalize_text(id_) for id_ in activity_identifiers)
    
    common = event_ids_normalized & activity_ids_normalized
    
    if common:
        score = 1.0
        matched = ", ".join(sorted(common))
        reasons.append(f"Exact identifier match: {matched}")
    
    return score, reasons