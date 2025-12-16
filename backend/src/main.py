from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from .config import CORS_ORIGINS, API_HOST, API_PORT
from .routers import (
    upload_router,
    search_router,
    ask_router,
    graph_router,
    validate_router
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("Запуск AeroDoc Assistant API...")
    yield
    # Shutdown
    logger.info("Остановка AeroDoc Assistant API...")


# Создание FastAPI приложения
app = FastAPI(
    title="AeroDoc Assistant API",
    description="API для работы с технической документацией авиастроения",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(upload_router)
app.include_router(search_router)
app.include_router(ask_router)
app.include_router(graph_router)
app.include_router(validate_router)


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "AeroDoc Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload",
            "search": "/search",
            "ask": "/ask",
            "graph": "/graph",
            "validate": "/validate",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья API"""
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик исключений"""
    logger.error(f"Необработанное исключение: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"}
    )


if __name__ == "__main__":
    import uvicorn
    import sys
    from pathlib import Path
    
    # Добавляем корень backend в путь для корректных импортов
    backend_root = Path(__file__).parent.parent
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    
    uvicorn.run(
        "src.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        reload_dirs=[str(backend_root / "src")]
    )

