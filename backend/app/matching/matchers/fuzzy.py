from rapidfuzz import fuzz
from typing import List
from app.models.progress import ProgressEvent
from app.models.schedule import ScheduleActivity


def fuzzy_match_score(event: ProgressEvent, activity: ScheduleActivity) -> tuple[float, List[str]]:
    reasons = []
    scores = []
    
    event_text = event.raw_text or ""
    if event.activity_reference:
        event_text += " " + event.activity_reference
    
    activity_text = activity.activity_name or ""
    
    ratio_score = fuzz.ratio(event_text.lower(), activity_text.lower()) / 100.0
    scores.append(ratio_score)
    
    if ratio_score > 0.8:
        reasons.append(f"High fuzzy match ({ratio_score:.0%}) between event text and activity name")
    elif ratio_score > 0.6:
        reasons.append(f"Moderate fuzzy match ({ratio_score:.0%}) between event text and activity name")
    
    if event.equipment_tag and activity.activity_name:
        equip_tag = event.equipment_tag.lower()
        activity_name_lower = activity.activity_name.lower()
        if equip_tag in activity_name_lower:
            equip_score = 1.0
            reasons.append(f"Equipment tag '{event.equipment_tag}' found in activity name")
        else:
            equip_score = fuzz.partial_ratio(equip_tag, activity_name_lower) / 100.0
            # Penalize partial matches on just numbers (e.g., "101" in "P-101")
            import re
            equip_numbers = re.findall(r'\d+', equip_tag)
            activity_numbers = re.findall(r'\d+', activity_name_lower)
            if equip_numbers and activity_numbers:
                common_numbers = set(equip_numbers) & set(activity_numbers)
                if common_numbers and len(common_numbers) == len(equip_numbers):
                    # Only numbers match, not the prefix - reduce score
                    equip_score = equip_score * 0.5
        scores.append(equip_score)
    
    if event.activity_reference and activity.activity_name:
        ref_score = fuzz.partial_ratio(event.activity_reference.lower(), activity.activity_name.lower()) / 100.0
        scores.append(ref_score)
        if ref_score > 0.7:
            reasons.append(f"Activity reference partial match ({ref_score:.0%})")
    
    event_discipline = (event.discipline or "").lower()
    activity_discipline = (activity.discipline or "").lower()
    if event_discipline and activity_discipline:
        disc_score = fuzz.ratio(event_discipline, activity_discipline) / 100.0
        scores.append(disc_score)
    
    event_location = (event.location or "").lower()
    activity_wbs = (activity.wbs or "").lower()
    if event_location and activity_wbs:
        loc_score = fuzz.partial_ratio(event_location, activity_wbs) / 100.0
        scores.append(loc_score)
        if loc_score > 0.7:
            reasons.append(f"Location/WBS fuzzy match ({loc_score:.0%})")
    
    final_score = max(scores) if scores else 0.0
    
    return final_score, reasons