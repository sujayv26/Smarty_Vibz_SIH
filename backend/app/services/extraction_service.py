from app.services.extraction_provider import BaseExtractionProvider
from app.services.mock_provider import MockExtractionProvider
from app.core.config import settings

_provider: BaseExtractionProvider | None = None

def get_extraction_provider() -> BaseExtractionProvider:
    global _provider
    if _provider is None:
        if settings.LLM_PROVIDER == "mock" or not settings.LLM_API_KEY:
            _provider = MockExtractionProvider()
        else:
            from app.services.llm_provider import LLMExtractionProvider
            _provider = LLMExtractionProvider(settings.LLM_API_KEY)
    return _provider

def set_extraction_provider(provider: BaseExtractionProvider) -> None:
    global _provider
    _provider = provider