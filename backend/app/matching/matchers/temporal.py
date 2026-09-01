from datetime import date, timedelta
from typing import List, Optional
from app.models.progress import ProgressEvent
from app.models.schedule import ScheduleActivity


def temporal_match_score(event: ProgressEvent, activity: ScheduleActivity) -> tuple[float, List[str]]:
    reasons = []
    event_date = event.event_date
    
    if not event_date:
        return 0.0, []
    
    planned_start = activity.planned_start
    planned_finish = activity.planned_finish
    
    if not planned_start or not planned_finish:
        return 0.0, []
    
    if planned_start <= event_date <= planned_finish:
        reasons.append(f"Event date {event_date} falls within planned window [{planned_start} - {planned_finish}]")
        return 1.0, reasons
    
    if event_date < planned_start:
        days_diff = (planned_start - event_date).days
        if days_diff <= 7:
            score = max(0.5, 1.0 - (days_diff / 14.0))
            reasons.append(f"Event date {event_date} is {days_diff} days before planned start (early)")
            return score, reasons
        else:
            reasons.append(f"Event date {event_date} is {days_diff} days before planned start")
            return 0.1, reasons
    
    if event_date > planned_finish:
        days_diff = (event_date - planned_finish).days
        if days_diff <= 7:
            score = max(0.3, 1.0 - (days_diff / 14.0))
            reasons.append(f"Event date {event_date} is {days_diff} days after planned finish (late)")
            return score, reasons
        else:
            reasons.append(f"Event date {event_date} is {days_diff} days after planned finish")
            return 0.05, reasons
    
    return 0.0, []