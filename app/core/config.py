from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Environment
    ENV: str = os.getenv("ENV", "dev")  # dev or prod
    
    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Game Jam API"
    
    # CORS Settings
    CORS_ORIGINS: list[str] = [
        # Dev origins
        "http://localhost:3000",
        "http://localhost:8000",
        # Add your prod origins here
        "https://dev.yourdomain.com",
        "https://yourdomain.com",
    ] if os.getenv("ENV") == "prod" else ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # API Keys
    MISTRAL_API_KEY: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Create a global settings instance
settings = get_settings() 