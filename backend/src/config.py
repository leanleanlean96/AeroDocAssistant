import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv(Path(__file__).parent.parent / "env" / "llm.env")

# Пути
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "dataset"
UPLOAD_DIR = BASE_DIR / "backend" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# LLM настройки
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
CATALOG_ID = os.getenv("CATALOG_ID")

# Qdrant настройки
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "aerodoc_documents")

# Embedding модель
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "ai-forever/ru-en-RoSBERTa")

# RAG настройки
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "300"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "1000"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.65"))

# API настройки
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")

# Кэширование
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 час

