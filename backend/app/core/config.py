from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    LLM_API_KEY: str = ""
    LLM_PROVIDER: str = "mock"
    DATABASE_URL: str = "sqlite:///./smarty_vibz.db"

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()