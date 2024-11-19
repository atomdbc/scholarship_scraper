# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Core settings
    PROJECT_NAME: str = "Striveopps Scholarship Scraper"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    AI_CHUNK_SIZE: int = 1000
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # Security settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./scholarships.db"
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Worker settings
    SCRAPING_INTERVAL: int = 3600  # Default 1 hour
    WORKER_BATCH_SIZE: int = 5
    SCRAPER_RATE_LIMIT: int = 1  # Requests per second
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # Seconds
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
        # Custom env file mappings
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name in ["ALLOWED_ORIGINS", "ALLOWED_HOSTS"]:
                if raw_val.startswith("[") and raw_val.endswith("]"):
                    return [x.strip(' "\'') for x in raw_val[1:-1].split(",")]
                return raw_val.split(",")
            return raw_val

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()