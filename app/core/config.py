from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from typing import Dict, Any

class Settings(BaseSettings):
    # Environment
    ENV: str = os.getenv("ENV", "dev")  # dev or prod
    
    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Game Jam API"
    
    # CORS Settings
    CORS_ORIGINS: list[str] = []  # Will be set based on environment
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API Keys
    MISTRAL_API_KEY: str
    
    # Environment-specific settings
    env_settings: Dict[str, Dict[str, Any]] = {
        "dev": {
            "cors_origins": ["*"],
            "log_level": "DEBUG",
            "api_timeout": 30,
            "max_requests_per_minute": 100,
        },
        "prod": {
            "cors_origins": [
                "https://game-jam-prod.yourdomain.com",
                "https://api.game-jam-prod.yourdomain.com"
            ],
            "log_level": "INFO",
            "api_timeout": 15,
            "max_requests_per_minute": 200,
        }
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.apply_env_settings()
    
    def apply_env_settings(self):
        """Apply environment-specific settings"""
        env = self.ENV.lower()
        if env not in self.env_settings:
            raise ValueError(f"Invalid environment: {env}")
            
        env_config = self.env_settings[env]
        
        # Apply environment-specific settings
        self.CORS_ORIGINS = env_config["cors_origins"]
        self.LOG_LEVEL = env_config["log_level"]
        
        # Add environment-specific attributes
        self.API_TIMEOUT = env_config["api_timeout"]
        self.MAX_REQUESTS_PER_MINUTE = env_config["max_requests_per_minute"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Create a global settings instance
settings = get_settings() 