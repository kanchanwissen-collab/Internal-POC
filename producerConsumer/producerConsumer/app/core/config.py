"""
Core configuration settings for the Producer-Consumer Batch API
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    app_name: str = "Producer-Consumer Batch API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    batch_endpoint_url: str = "http://localhost:8000/api/v1/batch/process"
    
    # Legacy field for backwards compatibility (will be ignored)
    consumer_endpoint_url: Optional[str] = None
    
    # Database Configuration
    mongodb_url: str = os.getenv("DATABASE_URL")
    mongodb_database: str = "batch_processing"
    mongodb_batch_collection: str = "batches"
    mongodb_items_collection: str = "batch_items"
    
    # Security Configuration
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Batch Processing Configuration
    max_batch_size: int = 1000
    batch_timeout_seconds: int = 30
    
    # Outbox Pattern Configuration
    outbox_poll_interval_seconds: int = 5
    outbox_batch_size: int = 100
    enable_outbox_processor: bool = True
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment
        env_file_encoding = 'utf-8'


# Global settings instance
settings = Settings()
