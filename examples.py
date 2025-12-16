"""
Примеры использования API для интеллектуального агента по технической документации
"""

import requests
import json
from typing import Dict, Any

# Базовый URL API
BASE_URL = "http://localhost:8000"


class DocumentClient:
    """Клиент для работы с API документов"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    # ===================== ДОКУМЕНТЫ =====================
    
    def create_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать новый документ"""
        response = requests.post(
            f"{self.base_url}/api/v1/documents",
            json=doc_data
        )
        return response.json()
    
    def get_all_documents(self) -> list:
        """Получить все документы"""
        response = requests.get(f"{self.base_url}/api/v1/documents")
        return response.json()
    
    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Получить документ по ID"""
        response = requests.get(f"{self.base_url}/api/v1/documents/{doc_id}")
        return response.json()
    
    def update_document(self, doc_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить документ"""
        response = requests.put(
            f"{self.base_url}/api/v1/documents/{doc_id}",
            json=update_data
        )
        return response.json()
    
    def delete_document(self, doc_id: str) -> bool:
        """Удалить документ"""
        response = requests.delete(f"{self.base_url}/api/v1/documents/{doc_id}")
        return response.status_code == 204
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        response = requests.get(f"{self.base_url}/api/v1/documents/stats/overview")
        return response.json()
    
    # ===================== ПОИСК И Q&A =====================
    
    def semantic_search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Семантический поиск"""
        response = requests.post(
            f"{self.base_url}/api/v1/search/semantic",
            json={"query": query, "top_k": top_k}
        )
        return response.json()
    
    def ask_question(self, question: str, top_k_context: int = 5) -> Dict[str, Any]:
        """Ответить на вопрос"""
        response = requests.post(
            f"{self.base_url}/api/v1/search/qa",
            json={"question": question, "top_k_context": top_k_context}
        )
        return response.json()
    
    def get_conversation_history(self, session_id: str) -> list:
        """Получить историю беседы"""
        response = requests.get(f"{self.base_url}/api/v1/search/history/{session_id}")
        return response.json()
    
    # ===================== ГРАФ И КОНСИСТЕНТНОСТЬ =====================
    
    def get_knowledge_graph(self) -> Dict[str, Any]:
        """Получить граф знаний"""
        response = requests.get(f"{self.base_url}/api/v1/graph")
        return response.json()
    
    def add_link(self, source_doc_id: str, target_doc_id: str, 
                link_type: str = "related", confidence: float = 1.0) -> Dict[str, Any]:
        """Добавить связь между документами"""
        response = requests.post(
            f"{self.base_url}/api/v1/graph/links",
            json={
                "source_doc_id": source_doc_id,
                "target_doc_id": target_doc_id,
                "link_type": link_type,
                "confidence": confidence
            }
        )
        return response.json()
    
    def get_related_documents(self, doc_id: str, max_depth: int = 2) -> list:
        """Получить связанные документы"""
        response = requests.get(
            f"{self.base_url}/api/v1/graph/related/{doc_id}",
            params={"max_depth": max_depth}
        )
        return response.json()
    
    def find_contradictions(self) -> list:
        """Найти противоречия"""
        response = requests.get(f"{self.base_url}/api/v1/graph/contradictions")
        return response.json()
    
    def check_consistency(self, doc_id: str) -> Dict[str, Any]:
        """Проверить консистентность документа"""
        response = requests.post(f"{self.base_url}/api/v1/graph/consistency/{doc_id}")
        return response.json()
    
    # ===================== СЛУЖЕБНЫЕ =====================
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья приложения"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def get_app_info(self) -> Dict[str, Any]:
        """Получить информацию о приложении"""
        response = requests.get(f"{self.base_url}/api/v1/info")
        return response.json()


# ===================== ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ =====================

def example_create_documents():
    """Пример: Создание документов"""
    client = DocumentClient()
    
    print("=" * 60)
    print("ПРИМЕР 1: Создание документов")
    print("=" * 60)
    
    # Документ 1: Чертеж
    doc1 = {
        "title": "Чертеж крыла МС-21",
        "content": "Основной чертеж конструкции крыла МС-21...",
        "document_type": "eskd",
        "doc_number": "МС-21-WG-001",
        "version": "3.2",
        "tags": ["wing", "MS-21"]
    }
    
    result1 = client.create_document(doc1)
    print(f"\nДокумент 1 создан: {result1.get('id')}")
    doc1_id = result1.get('id')
    
    # Документ 2: Сертификат материала
    doc2 = {
        "title": "Сертификат сплава АМГ6М",
        "content": "Алюминиевый сплав АМГ6М соответствует ГОСТ 4784...",
        "document_type": "material_cert",
        "doc_number": "ГОСТ 4784-97",
        "version": "1.0",
        "tags": ["aluminum", "material"]
    }
    
    result2 = client.create_document(doc2)
    print(f"Документ 2 создан: {result2.get('id')}")
    doc2_id = result2.get('id')
    
    return doc1_id, doc2_id


def example_search():
    """Пример: Семантический поиск"""
    client = DocumentClient()
    
    print("\n" + "=" * 60)
    print("ПРИМЕР 2: Семантический поиск")
    print("=" * 60)
    
    query = "Какие материалы используются при производстве крыла?"
    
    print(f"\nЗапрос: {query}")
    result = client.semantic_search(query, top_k=5)
    
    print(f"\nНайдено результатов: {result.get('total_results')}")
    print(f"Время выполнения: {result.get('execution_time_ms'):.2f} мс")
    
    for i, search_result in enumerate(result.get('results', []), 1):
        print(f"\n{i}. {search_result.get('title')}")
        print(f"   Релевантность: {search_result.get('relevance_score'):.2%}")
        print(f"   Превью: {search_result.get('content_preview')[:100]}...")


def example_qa():
    """Пример: Вопрос-ответ"""
    client = DocumentClient()
    
    print("\n" + "=" * 60)
    print("ПРИМЕР 3: Вопрос-ответ с цитированием источников")
    print("=" * 60)
    
    question = "Как выполнить ремонт радиатора при утечке?"
    
    print(f"\nВопрос: {question}")
    result = client.ask_question(question)
    
    print(f"\nОтвет: {result.get('answer')}")
    print(f"Уверенность: {result.get('confidence'):.2%}")
    
    print("\nИсточники:")
    for source in result.get('sources', []):
        print(f"- {source.get('title')} (релевантность: {source.get('relevance_score'):.2%})")


def example_graph():
    """Пример: Граф знаний"""
    client = DocumentClient()
    
    print("\n" + "=" * 60)
    print("ПРИМЕР 4: Граф знаний")
    print("=" * 60)
    
    # Получить граф
    graph = client.get_knowledge_graph()
    
    print(f"\nВсего узлов в графе: {graph.get('node_count')}")
    print(f"Всего связей: {graph.get('edge_count')}")
    
    print("\nТипы связей:")
    for node in graph.get('nodes', [])[:3]:
        print(f"- {node.get('label')} ({node.get('type')})")


def example_consistency():
    """Пример: Проверка консистентности"""
    client = DocumentClient()
    
    print("\n" + "=" * 60)
    print("ПРИМЕР 5: Проверка консистентности")
    print("=" * 60)
    
    # Сначала создать документ
    doc_data = {
        "title": "Руководство по ремонту (Старая версия)",
        "content": "Эта версия устарела. Используйте новую версию документа...",
        "document_type": "repair_manual",
        "version": "1.0",
        "status": "deprecated"
    }
    
    result = client.create_document(doc_data)
    doc_id = result.get('id')
    
    # Проверить консистентность
    consistency = client.check_consistency(doc_id)
    
    print(f"\nДокумент: {consistency.get('document_title')}")
    print(f"Найдено проблем: {len(consistency.get('issues', []))}")
    print(f"Предупреждений: {len(consistency.get('warnings', []))}")
    print(f"Устаревших ссылок: {len(consistency.get('deprecated_references', []))}")
    
    if consistency.get('warnings'):
        print("\nПредупреждения:")
        for warning in consistency.get('warnings'):
            print(f"- {warning.get('issue')}: {warning.get('message')}")


def example_statistics():
    """Пример: Получение статистики"""
    client = DocumentClient()
    
    print("\n" + "=" * 60)
    print("ПРИМЕР 6: Статистика системы")
    print("=" * 60)
    
    stats = client.get_statistics()
    
    print(f"\nВсего документов: {stats.get('total_documents')}")
    print(f"Документов в памяти: {stats.get('documents_in_memory')}")
    
    print("\nДокументы по типам:")
    for doc_type, count in stats.get('documents_by_type', {}).items():
        print(f"- {doc_type}: {count}")


def example_app_info():
    """Пример: Информация о приложении"""
    client = DocumentClient()
    
    print("\n" + "=" * 60)
    print("ПРИМЕР 7: Информация о приложении")
    print("=" * 60)
    
    info = client.get_app_info()
    
    app = info.get('application', {})
    print(f"\nНазвание: {app.get('name')}")
    print(f"Версия: {app.get('version')}")
    print(f"Описание: {app.get('description')}")
    
    config = info.get('configuration', {})
    print(f"\nМодель embeddings: {config.get('embedding_model')}")
    print(f"Размерность: {config.get('embedding_dimension')}")


if __name__ == "__main__":
    # Проверка подключения
    client = DocumentClient()
    
    try:
        health = client.health_check()
        print(f"✓ Приложение работает: {health.get('status')}\n")
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
        print("Убедитесь, что приложение запущено на http://localhost:8000")
        exit(1)
    
    # Запустить примеры
    try:
        doc1_id, doc2_id = example_create_documents()
        example_search()
        example_qa()
        example_graph()
        example_consistency()
        example_statistics()
        example_app_info()
        
        print("\n" + "=" * 60)
        print("✓ Все примеры выполнены успешно!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Ошибка при выполнении примеров: {e}")
        import traceback
        traceback.print_exc()
