# AeroDoc Assistant Backend

Backend API для работы с технической документацией авиастроения на базе FastAPI.

## Функционал (MVP)

- ✅ Семантический поиск по смыслу запроса
- ✅ Ответы с цитированием источников
- ✅ Граф связей между документами (Graph RAG)
- ✅ Проверка актуальности и противоречий

## Технологический стек

- **FastAPI** - веб-фреймворк
- **Qdrant** - векторная БД для эмбеддингов
- **YandexGPT** - LLM для генерации ответов
- **Sentence Transformers** - модели для создания эмбеддингов
- **NetworkX** - работа с графами
- **LangChain** - RAG-пайплайн

## Структура проекта

```
backend/
├── src/
│   ├── main.py                 # Точка входа FastAPI
│   ├── config.py               # Конфигурация
│   ├── models/                 # Pydantic модели
│   │   ├── schemas.py
│   │   └── __init__.py
│   ├── routers/                # API эндпоинты
│   │   ├── upload.py
│   │   ├── search.py
│   │   ├── ask.py
│   │   ├── graph.py
│   │   ├── validate.py
│   │   └── __init__.py
│   ├── services/               # Бизнес-логика
│   │   ├── document_service.py
│   │   ├── graph_service.py
│   │   ├── validation_service.py
│   │   ├── llm/
│   │   │   ├── main.py         # RAGModel
│   │   │   └── prompts/
│   │   └── __init__.py
│   └── utils/                  # Утилиты
│       ├── document_parser.py
│       ├── graph_builder.py
│       └── __init__.py
├── env/
│   └── llm.env                 # Переменные окружения
├── uploads/                    # Загруженные файлы
├── requirements.txt
└── README.md
```

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `env/llm.env` с переменными окружения:
```env
YANDEX_API_KEY=your_api_key
CATALOG_ID=your_catalog_id
QDRANT_COLLECTION_NAME=aerodoc_documents
EMBEDDING_MODEL=ai-forever/ru-en-RoSBERTa
```

3. Запустите сервер:
```bash
cd src
python main.py
```

Или через uvicorn:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## API Эндпоинты

### POST /upload
Загрузка и обработка документов

**Параметры:**
- `files`: список файлов (PDF, DOCX, JSON, XML)

**Ответ:**
```json
{
  "success": true,
  "message": "Обработано документов: 3",
  "documents_processed": 3,
  "document_ids": ["doc1", "doc2", "doc3"]
}
```

### POST /upload/dataset
Загрузка всех документов из датасета

### POST /search
Семантический поиск по документам

**Тело запроса:**
```json
{
  "query": "Какие требования к прочности крыла?",
  "limit": 10,
  "min_score": 0.65
}
```

**Ответ:**
```json
{
  "results": [
    {
      "content": "...",
      "score": 0.85,
      "citation": {
        "document_name": "SPEC-WING-001",
        "chapter": "4.2",
        "chunk_id": "...",
        "text": "..."
      },
      "metadata": {}
    }
  ],
  "total": 1
}
```

### POST /ask
Вопрос-ответ с цитированием

**Тело запроса:**
```json
{
  "question": "Какие требования к прочности крыла?",
  "documents": ["SPEC-WING-001"],
  "max_context_tokens": 1000
}
```

**Ответ:**
```json
{
  "answer": "Согласно документу SPEC-WING-001...",
  "citations": [
    {
      "document_name": "SPEC-WING-001",
      "chapter": "4.2",
      "chunk_id": "...",
      "text": "..."
    }
  ],
  "graph_links": ["doc_123", "doc_456"],
  "contradictions": false,
  "freshness": "2024-01-15"
}
```

### GET /graph/{doc_id}
Получить граф связей для документа

**Параметры:**
- `doc_id`: ID документа
- `depth`: глубина связей (по умолчанию 2)

**Ответ:**
```json
{
  "nodes": [
    {
      "id": "SPEC-WING-001",
      "type": "specification",
      "label": "Спецификация лонжерона",
      "metadata": {}
    }
  ],
  "edges": [
    {
      "source": "SPEC-WING-001",
      "target": "STD-045",
      "relation": "ссылается на стандарт",
      "weight": 1.0
    }
  ]
}
```

### GET /graph
Получить весь граф связей

### POST /validate
Проверка актуальности и противоречий

**Тело запроса:**
```json
{
  "document_ids": ["SPEC-WING-001", "STD-078"]
}
```

**Ответ:**
```json
{
  "obsolete_documents": [
    {
      "doc_id": "SPEC-FASTENERS-009",
      "title": "...",
      "type": "specification",
      "version": "1.0",
      "status": "устаревший",
      "issue_date": "2020-05-15"
    }
  ],
  "conflicts": [
    {
      "doc1": "STD-078",
      "doc2": "STD-189",
      "conflict_type": "противоречие в значениях",
      "description": "Разные значения моментов затяжки...",
      "severity": "высокая"
    }
  ],
  "outdated_references": [],
  "freshness_check": {
    "SPEC-WING-001": {
      "issue_date": "2023-11-15",
      "status": "актуальный",
      "is_obsolete": false
    }
  }
}
```

## Документация API

После запуска сервера документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Интеграция с фронтендом

API настроен для работы с фронтендом на React. CORS настроен для:
- http://localhost:3000
- http://localhost:3001

## Обработка документов

Поддерживаемые форматы:
- **JSON** - структурированные спецификации
- **XML** - стандарты
- **PDF** - чертежи, отчёты
- **DOCX** - руководства, техпроцессы

## RAG Pipeline

1. **Индексация:**
   - Парсинг документа
   - Разбивка на чанки
   - Создание эмбеддингов
   - Сохранение в Qdrant

2. **Retrieval:**
   - Семантический поиск по запросу
   - Фильтрация по score
   - Выбор релевантных чанков

3. **Generation:**
   - Формирование контекста
   - Генерация ответа через YandexGPT
   - Извлечение цитат

## Graph RAG

Граф связей строится на основе:
- `relations.json` - явные связи между документами
- `metadata.csv` - метаданные документов

Используется для:
- Поиска связанных документов
- Выявления противоречий
- Проверки актуальности

## Проверка противоречий

Система проверяет:
- Конфликты значений между документами
- Устаревшие ссылки на стандарты
- Актуальность документов по датам

## Кэширование

Часто запрашиваемые документы кэшируются для ускорения работы.

## Логирование

Все операции логируются с уровнем INFO. Ошибки логируются с полным traceback.

## Разработка

Для разработки с автоперезагрузкой:
```bash
uvicorn src.main:app --reload
```

## Лицензия

MIT

