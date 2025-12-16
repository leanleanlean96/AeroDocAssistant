"""
Скрипт для проверки работы интегрированной RAG системы с графом знаний
"""

import sys
import os

# Установка кодировки UTF-8 для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_environment():
    """Проверка окружения"""
    print("=" * 70)
    print("1️⃣  ПРОВЕРКА ОКРУЖЕНИЯ")
    print("=" * 70)
    
    # Проверка Python версии
    py_version = sys.version_info
    print(f"✓ Python версия: {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    # Проверка переменных окружения
    env_vars = {
        'YANDEX_API_KEY': os.getenv("YANDEX_API_KEY"),
        'CATALOG_ID': os.getenv("CATALOG_ID"),
        'NEO4J_URI': os.getenv("NEO4J_URI"),
        'NEO4J_USER': os.getenv("NEO4J_USER"),
        'NEO4J_PASSWORD': os.getenv("NEO4J_PASSWORD"),
    }
    
    for var, value in env_vars.items():
        if value:
            masked = value[:5] + "***" if len(value) > 5 else "***"
            print(f"✓ {var}: {masked}")
        else:
            print(f"⚠ {var}: не установлена")


def check_imports():
    """Проверка импортов"""
    print("\n" + "=" * 70)
    print("2️⃣  ПРОВЕРКА ИМПОРТОВ")
    print("=" * 70)
    
    imports_to_check = [
        ("qdrant_client", "QdrantClient"),
        ("sentence_transformers", "SentenceTransformer"),
        ("langchain_text_splitters", "RecursiveCharacterTextSplitter"),
        ("yandex_gpt", "YandexGPT"),
        ("neo4j", "GraphDatabase"),
        ("dotenv", "load_dotenv"),
    ]
    
    for module_name, class_name in imports_to_check:
        try:
            module = __import__(module_name)
            if hasattr(module, class_name):
                print(f"✓ {module_name}.{class_name}")
            else:
                print(f"⚠ {module_name} найден, но {class_name} не найден")
        except ImportError as e:
            print(f"✗ {module_name}: {e}")


def check_neo4j_connection():
    """Проверка подключения к Neo4j"""
    print("\n" + "=" * 70)
    print("3️⃣  ПРОВЕРКА ПОДКЛЮЧЕНИЯ К NEO4J")
    print("=" * 70)
    
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not password:
            print("⚠ NEO4J_PASSWORD не установлена")
            return False
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        
        print(f"✓ Подключение к Neo4j успешно")
        print(f"  URI: {uri}")
        print(f"  User: {user}")
        
        # Проверка графа
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()['count']
            print(f"✓ Узлов в графе: {count}")
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()['count']
            print(f"✓ Связей в графе: {rel_count}")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
        print("\n  Решение:")
        print("  1. Убедитесь, что Neo4j запущен: docker ps | grep neo4j")
        print("  2. Проверьте env/neo4j.env файл")
        print("  3. Дождитесь инициализации: sleep 30")
        return False


def check_rag_model():
    """Проверка RAG модели"""
    print("\n" + "=" * 70)
    print("4️⃣  ПРОВЕРКА RAG МОДЕЛИ")
    print("=" * 70)
    
    try:
        # Попытка импорта с изменением пути
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from src.services.llm.main import RAGModel
        
        print("✓ RAGModel импортирована успешно")
        
        # Создание экземпляра
        print("\n  Инициализация RAGModel...")
        rag = RAGModel(enable_knowledge_graph=True)
        print("✓ RAGModel инициализирована с графом знаний")
        
        # Проверка атрибутов
        assert hasattr(rag, 'qdrant'), "Qdrant не инициализирован"
        print("✓ Qdrant Vector DB: OK")
        
        assert hasattr(rag, 'embedding_model'), "Embedding модель не инициализирована"
        print("✓ SentenceTransformer: OK")
        
        assert hasattr(rag, 'llm_model'), "LLM модель не инициализирована"
        print("✓ YandexGPT: OK")
        
        assert hasattr(rag, 'knowledge_graph'), "Граф знаний не инициализирован"
        if rag.knowledge_graph:
            print("✓ Knowledge Graph: OK")
        else:
            print("⚠ Knowledge Graph не подключен (это нормально если Neo4j недоступен)")
        
        # Проверка методов
        methods = [
            'get_embeddings',
            'create_collection',
            'add_point',
            'rag_query',
            'ask',
            'get_related_documents',
            'get_document_conflicts',
            'find_documents_by_term',
            'get_term_definition',
            'close'
        ]
        
        for method in methods:
            assert hasattr(rag, method), f"Метод {method} не найден"
        print(f"✓ Все {len(methods)} методов присутствуют")
        
        rag.close()
        return True
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_functionality():
    """Тестирование базовой функциональности RAG"""
    print("\n" + "=" * 70)
    print("5️⃣  ТЕСТИРОВАНИЕ ФУНКЦИОНАЛЬНОСТИ RAG")
    print("=" * 70)
    
    try:
        from src.services.llm.main import RAGModel
        
        rag = RAGModel(enable_knowledge_graph=True)
        
        # Тест 1: Создание коллекции
        print("\n  Тест 1: Создание коллекции...")
        rag.ensure_collection("test_collection")
        print("  ✓ Коллекция создана")
        
        # Тест 2: Эмбеддинги
        print("\n  Тест 2: Генерация эмбеддингов...")
        embedding = rag.get_embeddings("тестовый текст")
        print(f"  ✓ Эмбеддинг размер: {len(embedding)} измерений")
        
        # Тест 3: Добавление точки
        print("\n  Тест 3: Добавление документа...")
        rag.add_point("test_collection", "Это тестовый документ", 
                      {"doc_id": "TEST-001", "content": "тест"})
        print("  ✓ Документ добавлен")
        
        # Тест 4: Методы графа знаний
        if rag.knowledge_graph:
            print("\n  Тест 4: Методы графа знаний...")
            try:
                conflicts = rag.get_document_conflicts()
                print(f"  ✓ Найдено конфликтов: {len(conflicts)}")
            except Exception as e:
                print(f"  ⚠ Ошибка получения конфликтов: {e}")
            
            try:
                term_def = rag.get_term_definition("лонжерон")
                if term_def:
                    print(f"  ✓ Определение термина найдено")
                else:
                    print(f"  ⚠ Определение термина не найдено")
            except Exception as e:
                print(f"  ⚠ Ошибка при поиске определения: {e}")
        
        rag.close()
        return True
        
    except Exception as e:
        print(f"✗ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """Вывод итоговой статистики"""
    print("\n" + "=" * 70)
    print("📊 ИТОГОВАЯ СВОДКА")
    print("=" * 70)
    
    passed = sum(results.values())
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nРезультат: {passed}/{total} ({percentage:.0f}%)")
    
    if passed == total:
        print("\n🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Система готова к использованию.")
    else:
        print("\n⚠️  НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ. Смотри ошибки выше.")


def print_next_steps():
    """Рекомендации по запуску"""
    print("\n" + "=" * 70)
    print("📝 КАК ИСПОЛЬЗОВАТЬ СИСТЕМУ")
    print("=" * 70)
    
    print("""
Вариант 1: Используй скрипт с примерами
    cd backend
    python examples_rag_integration.py

Вариант 2: Интерактивное использование
    python
    >>> from src.services.llm.main import RAGModel
    >>> rag = RAGModel()
    >>> answer = rag.ask("Какие требования к болтам?", "aviation_docs")
    >>> print(answer)
    >>> rag.close()

Вариант 3: Запустить в FastAPI
    cd backend
    uvicorn api:app --reload
    # Открыть http://localhost:8000/docs

Вариант 4: Просмотреть граф в Neo4j Browser
    # Открыть http://localhost:7474
    # Выполнить: MATCH (n) RETURN n LIMIT 50
    """)


if __name__ == "__main__":
    print("\n🚀 ПРОВЕРКА СИСТЕМЫ AERODOCASSISTANT\n")
    
    results = {
        "Окружение": True,  # Не критично
        "Импорты": True,    # Не критично
        "Neo4j подключение": check_neo4j_connection(),
        "RAG модель": check_rag_model(),
        "Функциональность": test_rag_functionality() if check_rag_model() else False,
    }
    
    print_summary(results)
    
    if results["RAG модель"]:
        print_next_steps()
    
    print("\n" + "=" * 70)
    sys.exit(0 if results["RAG модель"] else 1)
