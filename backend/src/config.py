"""Конфигурация приложения"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # API Sber
    sber_api_key: str = os.getenv("SBER_API_KEY", "default_key")
    sber_api_url: str = os.getenv("SBER_API_URL", "https://api.sber.ru/embeddings/v1")
    
    # База данных
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
    
    # Логирование
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    
    # Параметры embeddings
    embedding_model: str = "sber"
    embedding_dimension: int = 1024
    
    # Параметры поиска
    top_k_search: int = 5
    similarity_threshold: float = 0.3
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
