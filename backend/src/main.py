"""Основное приложение FastAPI"""
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict
from .config import settings
from .database.vector_db import VectorDatabase
from .services.embeddings_service import SberEmbeddingsService
from .services.document_service import DocumentService
from .services.rag_service import RAGService
from .services.graph_service import GraphService
from .routers import documents, search, graph

# Настройка логирования
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальные переменные для сервисов
app_context: Dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    
    # Инициализация при запуске
    logger.info("Initializing application...")
    
    try:
        # Инициализировать БД
        vector_db = VectorDatabase(settings.chroma_db_path)
        logger.info(f"Vector database initialized at {settings.chroma_db_path}")
        
        # Инициализировать embeddings сервис
        embeddings_service = SberEmbeddingsService(
            api_key=settings.sber_api_key,
            api_url=settings.sber_api_url
        )
        logger.info("Embeddings service initialized")
        
        # Инициализировать сервисы
        doc_service = DocumentService(vector_db, embeddings_service)
        rag_service = RAGService(doc_service, embeddings_service)
        graph_service = GraphService()
        
        # Сохранить в контексте
        app_context['vector_db'] = vector_db
        app_context['embeddings_service'] = embeddings_service
        app_context['doc_service'] = doc_service
        app_context['rag_service'] = rag_service
        app_context['graph_service'] = graph_service
        
        # Зарегистрировать роуты здесь, чтобы они были доступны уже при
        # формировании OpenAPI схемы и отображались в Swagger UI сразу после старта.
        try:
            app.include_router(documents.setup_document_routes(app_context['doc_service']))
            app.include_router(search.setup_search_routes(app_context['doc_service'], app_context['rag_service']))
            app.include_router(graph.setup_graph_routes(app_context['graph_service'], app_context['rag_service']))
            logger.info("Routers registered during lifespan initialization")
        except Exception as e:
            logger.warning(f"Failed to register routers during lifespan: {e}")

        logger.info("Application initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Очистка при остановке
    logger.info("Shutting down application...")
    try:
        await embeddings_service.close()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Создать FastAPI приложение
app = FastAPI(
    title="Aviation Technical Documentation Assistant",
    description="AI-powered RAG system for aviation technical documentation",
    version="1.0.0",
    lifespan=lifespan
)

# Добавить CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Роуты будут регистрироваться динамически после инициализации


@app.on_event("startup")
async def startup_event():
    """Событие при запуске"""
    # Роутеры уже регистрируются в `lifespan` при инициализации сервисов.
    logger.info("Startup event complete (routers registered in lifespan)")


@app.get("/health", tags=["health"])
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "healthy",
        "service": "Aviation Technical Documentation Assistant",
        "version": "1.0.0"
    }


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Редирект корневого пути на документацию"""
    return RedirectResponse(url="/docs")


@app.get("/api/v1/info", tags=["info"])
async def app_info():
    """Информация о приложении"""
    try:
        stats = app_context.get('doc_service', {}).get_statistics() if 'doc_service' in app_context else {}
        graph_stats = app_context.get('graph_service', {}).get_graph_statistics() if 'graph_service' in app_context else {}
        
        return {
            "application": {
                "name": "Aviation Technical Documentation Assistant",
                "version": "1.0.0",
                "description": "AI-powered RAG system for aviation technical documentation"
            },
            "configuration": {
                "embedding_model": settings.embedding_model,
                "embedding_dimension": settings.embedding_dimension,
                "top_k_search": settings.top_k_search,
                "similarity_threshold": settings.similarity_threshold,
            },
            "statistics": stats,
            "graph_statistics": graph_stats
        }
    except Exception as e:
        logger.error(f"Error getting app info: {e}")
        return {
            "application": {
                "name": "Aviation Technical Documentation Assistant",
                "version": "1.0.0",
            },
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
