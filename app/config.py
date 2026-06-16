import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "interview_forge"
    SECRET_KEY: str = "supersecretkey_interview_forge_123!"
    PRIMARY_PROVIDER: str = "gemini"
    
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None  # alternative for gemini
    OPENAI_API_KEY: Optional[str] = None
    CLAUDE_API_KEY: Optional[str] = None  # alternative for anthropic
    ANTHROPIC_API_KEY: Optional[str] = None # official SDK uses ANTHROPIC_API_KEY
    GROQ_API_KEY: Optional[str] = None
    
    @property
    def gemini_key(self) -> Optional[str]:
        return self.GEMINI_API_KEY or self.GOOGLE_API_KEY or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    @property
    def openai_key(self) -> Optional[str]:
        return self.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")

    @property
    def claude_key(self) -> Optional[str]:
        return self.CLAUDE_API_KEY or self.ANTHROPIC_API_KEY or os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

    @property
    def groq_key(self) -> Optional[str]:
        return self.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")

settings = Settings()
