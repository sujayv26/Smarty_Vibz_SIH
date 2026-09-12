import re
from typing import List
from app.models.progress import ProgressEvent
from app.models.schedule import ScheduleActivity


EVENT_TYPE_KEYWORDS = {
    "START": ["erect", "install", "start", "begin", "construct", "build", "assembly", "fabricat"],
    "PROGRESS": ["progress", "ongoing", "continuing", "in progress", "welding", "fitting"],
    "COMPLETE": ["complete", "finish", "done", "completed", "installed", "erected", "tested", "inspect", "hydrotest", "calibrat", "align"],
    "DELAY": ["delay", "late", "hold up", "postponed"],
    "HOLD": ["hold", "stop", "pause", "suspend", "on hold"],
}


def discipline_match_score(event: ProgressEvent, activity: ScheduleActivity) -> tuple[float, List[str]]:
    reasons = []
    event_disc = (event.discipline or "").lower().strip()
    activity_disc = (activity.discipline or "").lower().strip()
    
    if not event_disc or not activity_disc:
        return 0.0, []
    
    if event_disc == activity_disc:
        reasons.append(f"Discipline exact match: {event_disc}")
        return 1.0, reasons
    
    discipline_aliases = {
        "piping": ["pipe", "piping"],
        "civil": ["civil", "structural", "concrete", "foundation"],
        "mechanical": ["mechanical", "mech", "pump", "compressor", "rotating"],
        "electrical": ["electrical", "electric", "cable", "substation", "mcc", "terminat"],
        "instrumentation": ["instrumentation", "instrument", "calibrat", "transmitter", "tubing"],
        "structural": ["structural", "steel", "erect"],
    }
    
    for canonical, aliases in discipline_aliases.items():
        if event_disc in aliases and activity_disc in aliases:
            reasons.append(f"Discipline alias match: {event_disc} ~ {activity_disc}")
            return 0.8, reasons
    
    return 0.0, reasons


def wbs_context_score(event: ProgressEvent, activity: ScheduleActivity) -> tuple[float, List[str]]:
    reasons = []
    event_wbs_hint = ""
    
    if event.location:
        event_wbs_hint += event.location.lower() + " "
    if event.equipment_tag:
        event_wbs_hint += event.equipment_tag.lower() + " "
    if event.activity_reference:
        event_wbs_hint += event.activity_reference.lower()
    
    activity_wbs = (activity.wbs or "").lower()
    activity_name = (activity.activity_name or "").lower()
    
    if not event_wbs_hint.strip() or not activity_wbs:
        return 0.0, []
    
    event_tokens = set(event_wbs_hint.split())
    wbs_tokens = set(re.split(r"[.\-_/\s]+", activity_wbs + " " + activity_name))
    wbs_tokens = {t for t in wbs_tokens if len(t) > 2}
    
    common = event_tokens & wbs_tokens
    if common:
        score = min(len(common) / max(len(event_tokens), 1), 1.0)
        reasons.append(f"WBS/Context token overlap: {', '.join(sorted(common))}")
        return score, reasons
    
    return 0.0, reasons


def location_match_score(event: ProgressEvent, activity: ScheduleActivity) -> tuple[float, List[str]]:
    reasons = []
    event_loc = (event.location or "").lower().strip()
    activity_name = (activity.activity_name or "").lower()
    activity_wbs = (activity.wbs or "").lower()
    
    if not event_loc:
        return 0.0, []
    
    if event_loc in activity_name or event_loc in activity_wbs:
        reasons.append(f"Location '{event_loc}' found in activity")
        return 1.0, reasons
    
    loc_parts = event_loc.split()
    for part in loc_parts:
        if len(part) > 2 and (part in activity_name or part in activity_wbs):
            reasons.append(f"Location part '{part}' matches activity context")
            return 0.7, reasons
    
    return 0.0, reasons


def equipment_tag_match_score(event: ProgressEvent, activity: ScheduleActivity) -> tuple[float, List[str]]:
    reasons = []
    event_tag = (event.equipment_tag or "").upper().strip()
    activity_name = (activity.activity_name or "").upper()
    activity_code = (activity.activity_code or "").upper()
    
    if not event_tag:
        return 0.0, []
    
    if event_tag in activity_name or event_tag in activity_code:
        reasons.append(f"Equipment tag '{event_tag}' exactly matches activity")
        return 1.0, reasons
    
    return 0.0, reasons


def event_type_match_score(event: ProgressEvent, activity: ScheduleActivity) -> tuple[float, List[str]]:
    reasons = []
    event_type = (event.event_type or "").upper()
    activity_name = (activity.activity_name or "").lower()
    
    if not event_type or event_type not in EVENT_TYPE_KEYWORDS:
        return 0.0, []
    
    keywords = EVENT_TYPE_KEYWORDS[event_type]
    matches = [kw for kw in keywords if kw in activity_name]
    
    if matches:
        reasons.append(f"Event type '{event_type}' keywords match activity: {', '.join(matches)}")
        return 1.0, reasons
    
    return 0.0, reasons


def context_match_score(event: ProgressEvent, activity: ScheduleActivity) -> tuple[float, List[str]]:
    all_reasons = []
    scores = []
    
    disc_score, disc_reasons = discipline_match_score(event, activity)
    if disc_score > 0:
        scores.append(("discipline", disc_score))
        all_reasons.extend(disc_reasons)
    
    wbs_score, wbs_reasons = wbs_context_score(event, activity)
    if wbs_score > 0:
        scores.append(("wbs", wbs_score))
        all_reasons.extend(wbs_reasons)
    
    loc_score, loc_reasons = location_match_score(event, activity)
    if loc_score > 0:
        scores.append(("location", loc_score))
        all_reasons.extend(loc_reasons)
    
    equip_score, equip_reasons = equipment_tag_match_score(event, activity)
    if equip_score > 0:
        scores.append(("equipment", equip_score))
        all_reasons.extend(equip_reasons)
    
    type_score, type_reasons = event_type_match_score(event, activity)
    if type_score > 0:
        scores.append(("event_type", type_score))
        all_reasons.extend(type_reasons)
    
    if not scores:
        return 0.0, []
    
    final_score = sum(s for _, s in scores) / len(scores)
    return final_score, all_reasons