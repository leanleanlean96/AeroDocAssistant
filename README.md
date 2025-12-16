# Aviation Technical Documentation Assistant - Backend

Полнофункциональный backend на FastAPI для интеллектуального агента по авиационной технической документации.

## Особенности

### Основной функционал (MVP)
- ✅ Семантический поиск по смыслу запроса
- ✅ Управление документами (добавление, обновление, удаление)
- ✅ Ответы на вопросы с цитированием источников (RAG)
- ✅ Граф связей между документами
- ✅ Проверка актуальности и противоречий

### Технический стек
- **Framework**: FastAPI
- **Embeddings**: Sber Embeddings API
- **Vector DB**: Chroma
- **Graph**: NetworkX
- **Async**: AsyncIO, httpx

## Структура проекта

```
src/
├── main.py                 # Точка входа, инициализация приложения
├── config.py              # Конфигурация
├── models/
│   └── schemas.py         # Pydantic модели
├── services/
│   ├── embeddings_service.py   # Работа с Sber Embeddings
│   ├── document_service.py     # CRUD операции с документами
│   ├── rag_service.py          # RAG pipeline и Q&A
│   └── graph_service.py        # Управление графом знаний
├── database/
│   └── vector_db.py       # Работа с Chroma
├── routers/
│   ├── documents.py       # API для документов
│   ├── search.py          # API для поиска и Q&A
│   └── graph.py           # API для графа и консистентности
└── utils/                 # Утилиты

data/
└── chroma_db/            # Хранилище Chroma (создается автоматически)
```

## Установка и запуск

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
```bash
cp .env.example .env
# Отредактировать .env с вашими API ключами
```

### 3. Запуск приложения
```bash
cd src
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Приложение будет доступно по адресу: http://localhost:8000

### 4. Документация API
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Документы (Documents)
- `POST /api/v1/documents` - Создать документ
- `GET /api/v1/documents` - Получить все документы
- `GET /api/v1/documents/{doc_id}` - Получить документ
- `PUT /api/v1/documents/{doc_id}` - Обновить документ
- `DELETE /api/v1/documents/{doc_id}` - Удалить документ
- `GET /api/v1/documents/stats/overview` - Статистика

### Поиск и Q&A (Search)
- `POST /api/v1/search/semantic` - Семантический поиск
- `POST /api/v1/search/qa` - Ответить на вопрос
- `GET /api/v1/search/history/{session_id}` - История беседы
- `DELETE /api/v1/search/history/{session_id}` - Очистить историю

### Граф и Консистентность (Graph)
- `GET /api/v1/graph` - Получить граф знаний
- `POST /api/v1/graph/links` - Добавить связь
- `DELETE /api/v1/graph/links/{source_doc_id}/{target_doc_id}` - Удалить связь
- `GET /api/v1/graph/related/{doc_id}` - Связанные документы
- `GET /api/v1/graph/contradictions` - Найти противоречия
- `GET /api/v1/graph/statistics` - Статистика графа
- `POST /api/v1/graph/consistency/{doc_id}` - Проверить консистентность

### Служебные
- `GET /health` - Проверка здоровья
- `GET /api/v1/info` - Информация о приложении

## Примеры использования

### Создание документа
```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Руководство по ремонту МС-21",
    "content": "Документ содержит инструкции...",
    "document_type": "repair_manual",
    "doc_number": "МС-21-RM-001",
    "version": "1.0",
    "tags": ["repair", "MS-21"]
  }'
```

### Семантический поиск
```bash
curl -X POST http://localhost:8000/api/v1/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Какие требования к материалам для крыла?",
    "top_k": 5
  }'
```

### Ответить на вопрос
```bash
curl -X POST http://localhost:8000/api/v1/search/qa \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Как выполнить техническое обслуживание двигателя?"
  }'
```

## Архитектура системы

### RAG Pipeline
1. **Retrieval** - Поиск релевантных документов по embedding'у
2. **Augmentation** - Подготовка контекста из найденных документов
3. **Generation** - Генерация ответа на основе контекста

### Knowledge Graph
- Автоматическое построение связей между документами
- Выявление противоречий и устаревших ссылок
- Анализ центральности узлов

### Embedding Process
- Текст → Sber Embeddings API → 1024-размерный вектор
- Хранение в Chroma с метаданными
- Косинусное сходство для поиска

## Типы документов

- `ESKD` - Единая система конструкторской документации
- `ESTD` - Единая система технологической документации
- `REPAIR_MANUAL` - Руководство по ремонту
- `MATERIAL_CERT` - Сертификат материала
- `TEST_REPORT` - Отчет об испытаниях
- `STANDARD` - Отраслевой стандарт

## Статусы документов

- `active` - Активный (текущая версия)
- `archived` - Архивный (устаревший)
- `deprecated` - Устаревший (не использовать)

## Типы связей (Link Types)

- `related` - Связанный документ
- `references` - Ссылается на
- `contradicts` - Противоречит
- `updates` - Обновляет/заменяет

## Конфигурация

Основные параметры в `.env`:

```
SBER_API_KEY=your_key_here
SBER_API_URL=https://api.sber.ru/embeddings/v1
CHROMA_DB_PATH=./data/chroma_db
LOG_LEVEL=INFO
```

## Планы развития

### Фаза 2
- [ ] Интеграция с реальным LLM (OpenAI, GigaChat, YandexGPT)
- [ ] Поддержка мультимодальности (анализ чертежей)
- [ ] Голосовой интерфейс
- [ ] Авто-суммаризация документов

### Фаза 3
- [ ] Web UI на React/Vue
- [ ] Интеграция с системами документооборота
- [ ] Экспорт отчетов
- [ ] Мониторинг и аналитика

## Требования к базе знаний

Для максимальной эффективности системы необходимо:

1. **Структурированные данные**
   - Четкие названия документов
   - Правильное указание типов
   - Версионирование

2. **Метаданные**
   - Номер документа (ГОСТ, ESKD и т.д.)
   - Теги для категоризации
   - Статус документа

3. **Содержание**
   - Четкое изложение
   - Ссылки на связанные документы
   - Указание разделов и страниц

## Обработка ошибок

Все ошибки возвращаются в формате JSON:

```json
{
  "detail": "Описание ошибки",
  "status_code": 400
}
```

## Лицензия

MIT
