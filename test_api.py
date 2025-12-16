"""
Юнит-тесты для FastAPI приложения
"""

import pytest
import asyncio
from httpx import AsyncClient
from pathlib import Path
import sys

# Добавить src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backend.src.main import app
from backend.src.config import settings
from backend.src.models.schemas import DocumentCreate, DocumentType


@pytest.fixture
async def client():
    """Создать тестовый клиент"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    """Тест проверки здоровья приложения"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_app_info(client):
    """Тест информации о приложении"""
    response = await client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "application" in data
    assert data["application"]["name"] == "Aviation Technical Documentation Assistant"


@pytest.mark.asyncio
async def test_create_document(client):
    """Тест создания документа"""
    doc_data = {
        "title": "Тестовый документ",
        "content": "Содержание тестового документа",
        "document_type": "repair_manual",
        "version": "1.0",
        "tags": ["test"]
    }
    
    response = await client.post("/api/v1/documents", json=doc_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == doc_data["title"]
    assert "id" in data


@pytest.mark.asyncio
async def test_get_all_documents(client):
    """Тест получения всех документов"""
    # Сначала создать документ
    doc_data = {
        "title": "Тестовый документ для списка",
        "content": "Содержание",
        "document_type": "standard",
        "version": "1.0"
    }
    
    create_response = await client.post("/api/v1/documents", json=doc_data)
    assert create_response.status_code == 201
    
    # Получить все документы
    response = await client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_semantic_search(client):
    """Тест семантического поиска"""
    # Создать документ
    doc_data = {
        "title": "Документация по авиации",
        "content": "Информация о материалах для самолета",
        "document_type": "standard",
        "version": "1.0"
    }
    
    create_response = await client.post("/api/v1/documents", json=doc_data)
    assert create_response.status_code == 201
    
    # Выполнить поиск
    search_data = {
        "query": "материалы самолета",
        "top_k": 5
    }
    
    response = await client.post("/api/v1/search/semantic", json=search_data)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "query" in data


@pytest.mark.asyncio
async def test_question_answer(client):
    """Тест вопрос-ответ"""
    # Создать документ
    doc_data = {
        "title": "Руководство по ремонту",
        "content": "Для ремонта требуется выполнить следующие шаги...",
        "document_type": "repair_manual",
        "version": "1.0"
    }
    
    create_response = await client.post("/api/v1/documents", json=doc_data)
    assert create_response.status_code == 201
    
    # Задать вопрос
    qa_data = {
        "question": "Как выполнить ремонт?",
        "top_k_context": 5
    }
    
    response = await client.post("/api/v1/search/qa", json=qa_data)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "confidence" in data


@pytest.mark.asyncio
async def test_get_knowledge_graph(client):
    """Тест получения графа знаний"""
    response = await client.get("/api/v1/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data


@pytest.mark.asyncio
async def test_get_statistics(client):
    """Тест получения статистики"""
    response = await client.get("/api/v1/documents/stats/overview")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data


@pytest.mark.asyncio
async def test_update_document(client):
    """Тест обновления документа"""
    # Создать документ
    doc_data = {
        "title": "Документ для обновления",
        "content": "Исходное содержание",
        "document_type": "standard",
        "version": "1.0"
    }
    
    create_response = await client.post("/api/v1/documents", json=doc_data)
    assert create_response.status_code == 201
    doc_id = create_response.json()["id"]
    
    # Обновить документ
    update_data = {
        "version": "2.0",
        "status": "archived"
    }
    
    response = await client.put(f"/api/v1/documents/{doc_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.0"
    assert data["status"] == "archived"


@pytest.mark.asyncio
async def test_delete_document(client):
    """Тест удаления документа"""
    # Создать документ
    doc_data = {
        "title": "Документ для удаления",
        "content": "Содержание",
        "document_type": "standard",
        "version": "1.0"
    }
    
    create_response = await client.post("/api/v1/documents", json=doc_data)
    assert create_response.status_code == 201
    doc_id = create_response.json()["id"]
    
    # Удалить документ
    response = await client.delete(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_document_not_found(client):
    """Тест попытки получить несуществующий документ"""
    response = await client.get("/api/v1/documents/nonexistent_id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_document_type(client):
    """Тест создания документа с неверным типом"""
    doc_data = {
        "title": "Документ",
        "content": "Содержание",
        "document_type": "invalid_type",  # Неверный тип
        "version": "1.0"
    }
    
    response = await client.post("/api/v1/documents", json=doc_data)
    # FastAPI валидирует enum, поэтому должна быть ошибка
    assert response.status_code >= 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
