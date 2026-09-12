from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.progress import ProgressEvent
from app.models.schedule import ScheduleActivity
from app.core.config import settings


class SemanticMatcher(ABC):
    @abstractmethod
    def match(self, event: ProgressEvent, activity: ScheduleActivity) -> tuple[float, List[str]]:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass


class OfflineSemanticMatcher(SemanticMatcher):
    def __init__(self):
        self._keyword_weights = {
            "erection": 0.8, "erect": 0.8, "install": 0.7, "installation": 0.7,
            "support": 0.6, "inspect": 0.6, "inspection": 0.6, "hydrotest": 0.7,
            "calibrat": 0.7, "align": 0.6, "pulling": 0.6, "terminat": 0.6,
            "pour": 0.7, "concrete": 0.6, "foundation": 0.6, "structural": 0.5,
            "steel": 0.5, "weld": 0.5, "fabricat": 0.5, "assembly": 0.5,
            "pump": 0.6, "compressor": 0.6, "cable": 0.6, "substation": 0.5,
            "mcc": 0.5, "panel": 0.5, "instrument": 0.5, "transmitter": 0.5,
            "tubing": 0.5,
        }
    
    def is_available(self) -> bool:
        return True
    
    def match(self, event: ProgressEvent, activity: ScheduleActivity) -> tuple[float, List[str]]:
        reasons = []
        event_text = (event.raw_text or "").lower()
        if event.activity_reference:
            event_text += " " + event.activity_reference.lower()
        
        activity_text = (activity.activity_name or "").lower()
        
        event_keywords = set()
        for kw, weight in self._keyword_weights.items():
            if kw in event_text:
                event_keywords.add((kw, weight))
        
        activity_keywords = set()
        for kw, weight in self._keyword_weights.items():
            if kw in activity_text:
                activity_keywords.add((kw, weight))
        
        if not event_keywords or not activity_keywords:
            return 0.0, []
        
        event_kw_dict = dict(event_keywords)
        activity_kw_dict = dict(activity_keywords)
        
        common_keywords = set(event_kw_dict.keys()) & set(activity_kw_dict.keys())
        
        if not common_keywords:
            return 0.0, []
        
        total_weight = sum(event_kw_dict.get(kw, 0) + activity_kw_dict.get(kw, 0) for kw in common_keywords)
        max_possible = sum(event_kw_dict.values()) + sum(activity_kw_dict.values())
        
        if max_possible == 0:
            return 0.0, []
        
        score = total_weight / max_possible
        
        if score > 0.5:
            reasons.append(f"Semantic keyword overlap: {', '.join(sorted(common_keywords))}")
        
        return min(score, 1.0), reasons


class LLMSemanticMatcher(SemanticMatcher):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._offline_fallback = OfflineSemanticMatcher()
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def match(self, event: ProgressEvent, activity: ScheduleActivity) -> tuple[float, List[str]]:
        if not self.is_available():
            return self._offline_fallback.match(event, activity)
        
        try:
            return self._call_llm_semantic_match(event, activity)
        except Exception:
            return self._offline_fallback.match(event, activity)
    
    def _call_llm_semantic_match(self, event: ProgressEvent, activity: ScheduleActivity) -> tuple[float, List[str]]:
        return self._offline_fallback.match(event, activity)


def get_semantic_matcher() -> SemanticMatcher:
    if settings.LLM_PROVIDER != "mock" and settings.LLM_API_KEY:
        return LLMSemanticMatcher(settings.LLM_API_KEY)
    return OfflineSemanticMatcher()