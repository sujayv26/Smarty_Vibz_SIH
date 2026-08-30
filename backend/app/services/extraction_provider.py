from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.progress import ProgressEventCreate
from app.schemas.agent import UnderstoodProgress

class BaseExtractionProvider(ABC):
    @abstractmethod
    def extract_progress(self, raw_text: str) -> ProgressEventCreate:
        pass

    @abstractmethod
    def extract_agent_chat(self, message: str, context: Optional[dict] = None) -> UnderstoodProgress:
        pass