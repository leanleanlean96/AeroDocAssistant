"""
АРХИТЕКТУРА СИСТЕМЫ
Aviation Technical Documentation Assistant - Backend
"""

# ============================================================================
# АРХИТЕКТУРА СИСТЕМЫ
# ============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (опционально)                          │
│              (React / Vue / Streamlit / Gradio)                         │
└────────────────────────────┬────────────────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────▼────────────────────────────────────────────┐
│                                                                          │
│                         FASTAPI APPLICATION                             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                       API LAYER (Routers)                        │  │
│  │  ┌──────────────┬──────────────┬──────────────┐                │  │
│  │  │  Documents   │  Search/QA   │   Graph/     │                │  │
│  │  │     API      │     API      │ Consistency  │                │  │
│  │  └──────────┬───┴──────────┬───┴──────┬──────┘                 │  │
│  └─────────────┼──────────────┼──────────┼────────────────────────┘  │
│                │              │          │                             │
│  ┌─────────────▼──────────────▼──────────▼────────────────────────┐  │
│  │                    SERVICE LAYER                              │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │ DocumentService  │  RAGService  │  GraphService        │ │  │
│  │  │                  │              │                       │ │  │
│  │  │ - Create/Read/   │ - Answer Q&A │ - Node management    │ │  │
│  │  │   Update/Delete  │ - Consistency│ - Link management    │ │  │
│  │  │ - Embedding gen. │   check      │ - Visualization      │ │  │
│  │  │                  │ - Conv. hist │ - Analytics          │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  │                                                                  │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │        EmbeddingsService (Sber Embeddings)              │ │  │
│  │  │  - Text → 1024-dim vector conversion                    │ │  │
│  │  │  - Batch processing                                     │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  │                                                                  │  │
│  └────────────────────┬────────────────────┬──────────────────────┘  │
│                       │                    │                         │
└───────────────────────┼────────────────────┼─────────────────────────┘
                        │                    │
         ┌──────────────▼────┐    ┌──────────▼──────────┐
         │   Vector Database │    │  Knowledge Graph    │
         │      (Chroma)     │    │    (NetworkX)       │
         │                   │    │                     │
         │ - Embeddings      │    │ - Nodes             │
         │ - Documents       │    │ - Edges/Links       │
         │ - Metadata        │    │ - Centrality        │
         │ - Search          │    │ - Paths             │
         └───────────────────┘    └─────────────────────┘
              File Storage            In-Memory


┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA MODELS                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Document:                                                              │
│  ├── id: UUID                                                          │
│  ├── title: str                                                        │
│  ├── content: str                                                      │
│  ├── type: DocumentType (eskd|estd|repair_manual|...)                 │
│  ├── doc_number: str (ГОСТ, ESKD и т.д.)                             │
│  ├── version: str                                                      │
│  ├── status: str (active|archived|deprecated)                         │
│  ├── tags: List[str]                                                   │
│  ├── metadata: Dict[str, Any]                                          │
│  ├── embedding: List[float] (1024-dim)                                │
│  └── timestamps: created_at, updated_at                              │
│                                                                         │
│  Link:                                                                  │
│  ├── source_doc_id: UUID                                              │
│  ├── target_doc_id: UUID                                              │
│  ├── link_type: str (related|references|contradicts|updates)          │
│  ├── confidence: float [0-1]                                          │
│  └── description: str                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
"""

# ============================================================================
# КОМПОНЕНТЫ И ИХ ОТВЕТСТВЕННОСТЬ
# ============================================================================

COMPONENTS = {
    "main.py": {
        "description": "Точка входа приложения",
        "responsibilities": [
            "Инициализация FastAPI приложения",
            "Управление жизненным циклом (startup/shutdown)",
            "Подключение middleware (CORS)",
            "Регистрация routers",
            "Health checks"
        ]
    },
    
    "config.py": {
        "description": "Конфигурация приложения",
        "responsibilities": [
            "Загрузка переменных окружения",
            "Валидация конфигурации",
            "Предоставление глобальных настроек"
        ]
    },
    
    "models/schemas.py": {
        "description": "Pydantic модели для валидации",
        "responsibilities": [
            "Определение структур данных",
            "Валидация входных данных",
            "Сериализация ответов",
            "Типизация"
        ]
    },
    
    "database/vector_db.py": {
        "description": "Работа с Chroma БД",
        "responsibilities": [
            "Добавление документов с embeddings",
            "Удаление документов",
            "Обновление документов",
            "Поиск по similarity",
            "Метаданные документов"
        ]
    },
    
    "services/embeddings_service.py": {
        "description": "Работа с embeddings",
        "responsibilities": [
            "Преобразование текста в embeddings",
            "Работа с Sber API",
            "Кеширование результатов",
            "Batch processing",
            "Обработка ошибок"
        ]
    },
    
    "services/document_service.py": {
        "description": "Управление документами (CRUD)",
        "responsibilities": [
            "Создание документов",
            "Чтение документов",
            "Обновление документов",
            "Удаление документов",
            "Поиск документов",
            "Статистика"
        ]
    },
    
    "services/rag_service.py": {
        "description": "RAG pipeline",
        "responsibilities": [
            "Ответы на вопросы (Q&A)",
            "Retrieval релевантных документов",
            "Подготовка контекста",
            "Генерация ответов",
            "История беседы",
            "Проверка консистентности"
        ]
    },
    
    "services/graph_service.py": {
        "description": "Управление графом знаний",
        "responsibilities": [
            "Добавление узлов/ребер",
            "Поиск связей между документами",
            "Выявление противоречий",
            "Анализ графа (центральность и т.д.)",
            "Визуализация"
        ]
    },
    
    "routers/documents.py": {
        "description": "API endpoints для документов",
        "responsibilities": [
            "POST /documents - создание",
            "GET /documents - список",
            "GET /documents/{id} - деталь",
            "PUT /documents/{id} - обновление",
            "DELETE /documents/{id} - удаление",
            "GET /documents/stats - статистика"
        ]
    },
    
    "routers/search.py": {
        "description": "API endpoints для поиска и Q&A",
        "responsibilities": [
            "POST /search/semantic - семантический поиск",
            "POST /search/qa - вопрос-ответ",
            "GET /search/history - история",
            "DELETE /search/history - очистка"
        ]
    },
    
    "routers/graph.py": {
        "description": "API endpoints для графа",
        "responsibilities": [
            "GET /graph - получить граф",
            "POST /graph/links - добавить связь",
            "DELETE /graph/links - удалить связь",
            "GET /graph/related - связанные документы",
            "GET /graph/contradictions - противоречия",
            "POST /graph/consistency - проверка"
        ]
    }
}

# ============================================================================
# ПОТОКИ ДАННЫХ
# ============================================================================

WORKFLOWS = {
    "Создание документа": """
    1. Фронтенд отправляет POST /documents
    2. API валидирует данные (schemas.py)
    3. DocumentService получает embedding через EmbeddingsService
    4. VectorDatabase сохраняет документ с embedding
    5. GraphService добавляет узел в граф
    6. Возвращается информация о документе
    """,
    
    "Семантический поиск": """
    1. Фронтенд отправляет POST /search/semantic с query
    2. EmbeddingsService преобразует query в embedding
    3. VectorDatabase ищет похожие документы (cosine similarity)
    4. Результаты преобразуются в SearchResult
    5. Возвращаются TOP-K результатов с релевантностью
    """,
    
    "Вопрос-ответ (RAG)": """
    1. Фронтенд отправляет POST /search/qa с вопросом
    2. RAGService выполняет поиск релевантных документов
    3. Подготавливается контекст из найденных документов
    4. Генерируется ответ (демо: простое резюме контекста)
    5. В продакшене: вызов LLM (OpenAI, GigaChat и т.д.)
    6. Возвращается ответ с источниками и уверенностью
    """,
    
    "Построение графа": """
    1. Документы добавляются в граф как узлы
    2. Автоматически анализируются связи между документами
    3. GraphService добавляет ребра с типом связи
    4. Можно явно добавлять связи через API
    5. Graph визуализируется и анализируется
    """,
    
    "Проверка консистентности": """
    1. Фронтенд отправляет POST /graph/consistency/{doc_id}
    2. RAGService анализирует документ на предмет:
       - Устаревших ссылок
       - Противоречивых требований
       - Версионирования
       - Актуальности
    3. Возвращается отчет с найденными проблемами
    """
}

# ============================================================================
# ТИПЫ ДАННЫХ И ВАЛИДАЦИЯ
# ============================================================================

DATA_TYPES = {
    "DocumentType": [
        "eskd - Конструкторская документация",
        "estd - Технологическая документация",
        "repair_manual - Руководство по ремонту",
        "material_cert - Сертификат материала",
        "test_report - Отчет об испытаниях",
        "standard - Отраслевой стандарт",
        "other - Прочее"
    ],
    
    "LinkType": [
        "related - Связанный документ",
        "references - Ссылается на",
        "contradicts - Противоречит",
        "updates - Обновляет/заменяет"
    ],
    
    "DocumentStatus": [
        "active - Активный документ",
        "archived - Архивный",
        "deprecated - Устаревший"
    ]
}

# ============================================================================
# МАСШТАБИРОВАНИЕ И ОПТИМИЗАЦИЯ
# ============================================================================

OPTIMIZATION_TIPS = """
Текущее состояние (MVP):
- Работает для 10,000+ документов
- Embeddings: mock генератор (готово к Sber API)
- Graph: in-memory (NetworkX)
- Search: <100ms для типичного запроса

Для масштабирования:

1. Embeddings:
   - Используйте настоящий Sber API (настроено)
   - Добавьте Redis кеширование
   - Batch embeddings генерацию

2. Vector DB:
   - Замените Chroma на Qdrant для больших объемов
   - Добавьте индексирование
   - Используйте разные индексы по типам документов

3. Graph:
   - Переместите в PostgreSQL + networkx для больших графов
   - Добавьте кеширование часто запрашиваемых путей
   - Используйте параллельные вычисления центральности

4. API:
   - Используйте несколько инстансов FastAPI за Nginx
   - Добавьте Rate limiting
   - Используйте асинхронные задачи (Celery/Redis)

5. LLM интеграция:
   - Добавьте поддержку разных LLM провайдеров
   - Кешируйте результаты генерации
   - Используйте streaming responses для больших ответов
"""

# ============================================================================
# БЕЗОПАСНОСТЬ
# ============================================================================

SECURITY_CONSIDERATIONS = """
Текущая реализация (MVP):
- Нет аутентификации (добавить при prodакшене)
- CORS настроен для локального развития
- Нет rate limiting
- Логирование минимально

Для продакшена добавить:

1. Аутентификация:
   - JWT токены
   - OAuth2 интеграция
   - API ключи для сервис-сервис

2. Авторизация:
   - Role-based access control (RBAC)
   - Document-level permissions
   - Audit logging

3. Защита данных:
   - Шифрование sensitive данных
   - Validation всех входных данных
   - SQL injection защита (используем ORM)
   - XSS/CSRF защита

4. Мониторинг:
   - Request/response logging
   - Performance monitoring
   - Error tracking (Sentry)
   - Security alerts
"""

if __name__ == "__main__":
    print(__doc__)
    print("\n" + "="*80)
    print("КОМПОНЕНТЫ")
    print("="*80)
    for comp, info in COMPONENTS.items():
        print(f"\n📦 {comp}")
        print(f"   {info['description']}")
        for resp in info['responsibilities']:
            print(f"   • {resp}")
    
    print("\n" + "="*80)
    print("ПОТОКИ ДАННЫХ")
    print("="*80)
    for workflow, description in WORKFLOWS.items():
        print(f"\n🔄 {workflow}")
        print(description)
    
    print("\n" + "="*80)
    print("ОПТИМИЗАЦИЯ")
    print("="*80)
    print(OPTIMIZATION_TIPS)
    
    print("\n" + "="*80)
    print("БЕЗОПАСНОСТЬ")
    print("="*80)
    print(SECURITY_CONSIDERATIONS)
