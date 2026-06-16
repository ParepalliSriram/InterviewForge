import os
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    MONGODB_URI: str = "mongodb://localhost:27017"

    @model_validator(mode="before")
    @classmethod
    def populate_mongodb_uri(cls, data):
        # We check common env vars for MongoDB URI in order of priority
        keys = ["MONGODB_URI", "MONGO_URI", "MONGODB_URL", "MONGO_URL"]
        
        # 1. Check data dict (which includes loaded env vars and dotenv values)
        if isinstance(data, dict):
            for key in keys:
                if key in data and data[key]:
                    data["MONGODB_URI"] = data[key]
                    return data
                if key.lower() in data and data[key.lower()]:
                    data["MONGODB_URI"] = data[key.lower()]
                    return data
        
        # 2. Check os.environ directly
        for key in keys:
            val = os.environ.get(key)
            if val:
                if isinstance(data, dict):
                    data["MONGODB_URI"] = val
                    return data
        return data
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
