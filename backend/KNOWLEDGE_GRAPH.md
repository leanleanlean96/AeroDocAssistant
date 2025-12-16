# Граф знаний для AeroDocAssistant

Этот модуль реализует граф знаний на базе Neo4j для авиационной технической документации.

## Структура графа

### Типы узлов

1. **Document** - документы различных типов:
   - specification (спецификации)
   - standard (стандарты)
   - drawing (чертежи)
   - manual (руководства)
   - report (отчёты)
   - tech_process (техпроцессы)

2. **Section** - секции документов с детальным контентом

3. **Term** - термины из глоссария

4. **Abbreviation** - аббревиатуры

5. **Conflict** - конфликты между документами

6. **ObsoleteReference** - устаревшие ссылки

### Типы связей

- `RELATES_TO` - общая связь между документами
- `HAS_SECTION` - документ содержит секцию
- `MENTIONS` - документ упоминает термин
- `RELATED_TO` - связь между терминами
- `HAS_CONFLICT` - документ имеет конфликт
- `HAS_OBSOLETE_REFERENCE` - документ содержит устаревшую ссылку

## Установка и настройка

### 1. Установка Neo4j

**Windows (Docker):**
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:latest
```

**Windows (без Docker):**
1. Скачайте Neo4j Desktop с https://neo4j.com/download/
2. Установите и создайте новую базу данных
3. Запустите базу данных

### 2. Настройка переменных окружения

Отредактируйте файл `backend/env/neo4j.env`:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

### 3. Установка зависимостей

```bash
cd backend
pip install neo4j python-dotenv
```

## Использование

### Построение графа знаний

```python
from src.services.knowledge_graph import KnowledgeGraphBuilder

# Создание построителя графа
builder = KnowledgeGraphBuilder()

try:
    # Построение полного графа из всех данных
    builder.build_knowledge_graph()
    
    # Получение статистики
    stats = builder.get_statistics()
    print(f"Всего узлов: {stats['total_nodes']}")
    print(f"Всего связей: {stats['total_relationships']}")
finally:
    builder.close()
```

Или запустить из командной строки:

```bash
cd backend
python -m src.services.knowledge_graph
```

### Выполнение запросов

```python
from src.services.knowledge_graph_queries import KnowledgeGraphQueries

queries = KnowledgeGraphQueries()

try:
    # Найти связанные документы
    related = queries.find_related_documents("SPEC-WING-001", max_depth=2)
    
    # Найти конфликты
    conflicts = queries.find_conflicts()
    
    # Найти документы по термину
    docs = queries.find_documents_by_term("лонжерон")
    
    # Поиск по содержимому
    results = queries.search_documents_by_content("затяжка")
finally:
    queries.close()
```

Демонстрация всех запросов:

```bash
cd backend
python -m src.services.knowledge_graph_queries
```

## Примеры запросов Cypher

### Найти все документы, связанные со спецификацией

```cypher
MATCH (spec:Document {doc_id: 'SPEC-WING-001'})-[r:RELATES_TO*1..2]->(related:Document)
RETURN related.doc_id, related.title, related.type
```

### Найти конфликты высокой критичности

```cypher
MATCH (d1:Document)-[:HAS_CONFLICT]->(c:Conflict {severity: 'высокая'})<-[:HAS_CONFLICT]-(d2:Document)
RETURN d1.title, d2.title, c.description
```

### Найти устаревшие документы и их замены

```cypher
MATCH (old:Document {status: 'устаревший'})<-[r:RELATES_TO]-(new:Document)
WHERE r.type CONTAINS 'заменён'
RETURN old.doc_id, old.title, new.doc_id, new.title
```

### Найти цепочку зависимостей документа

```cypher
MATCH path = (start:Document {doc_id: 'SPEC-WING-001'})-[:RELATES_TO*]->(end:Document)
RETURN path
LIMIT 10
```

### Найти термины, связанные с документом

```cypher
MATCH (d:Document {doc_id: 'SPEC-WING-001'})-[:MENTIONS]->(t:Term)
RETURN t.term, t.definition
```

### Анализ влияния изменения стандарта

```cypher
MATCH (std:Document {doc_id: 'STD-045'})<-[:RELATES_TO*]-(affected:Document)
RETURN DISTINCT affected.doc_id, affected.title, affected.type
ORDER BY affected.type
```

## Интеграция с RAG

Граф знаний может быть использован для улучшения RAG-системы:

1. **Расширение контекста**: При поиске документа автоматически включать связанные документы
2. **Разрешение конфликтов**: Предупреждать о противоречиях в документации
3. **Навигация**: Предлагать связанные документы пользователю
4. **Проверка актуальности**: Предупреждать об устаревших ссылках

### Пример интеграции

```python
from src.services.llm.main import RAGModel
from src.services.knowledge_graph_queries import KnowledgeGraphQueries

class EnhancedRAG:
    def __init__(self):
        self.rag = RAGModel()
        self.kg = KnowledgeGraphQueries()
        
    def query_with_context(self, query: str, doc_id: str):
        # Найти связанные документы из графа
        related = self.kg.find_related_documents(doc_id)
        
        # Расширить контекст для RAG
        # ... ваша логика
        
        # Проверить конфликты
        conflicts = self.kg.find_conflicts()
        # ... обработка конфликтов
```

## API для веб-приложения

Создайте REST API endpoint в FastAPI:

```python
from fastapi import FastAPI, HTTPException
from src.services.knowledge_graph_queries import KnowledgeGraphQueries

app = FastAPI()
kg_queries = KnowledgeGraphQueries()

@app.get("/api/graph/document/{doc_id}/related")
async def get_related_documents(doc_id: str, max_depth: int = 2):
    """Получить связанные документы"""
    return kg_queries.find_related_documents(doc_id, max_depth)

@app.get("/api/graph/conflicts")
async def get_conflicts():
    """Получить все конфликты"""
    return kg_queries.find_conflicts()

@app.get("/api/graph/search")
async def search_documents(q: str):
    """Поиск документов по содержимому"""
    return kg_queries.search_documents_by_content(q)
```

## Визуализация

Используйте Neo4j Browser для визуализации графа:

1. Откройте http://localhost:7474
2. Выполните запросы Cypher для просмотра графа

Пример визуализации всех связей SPEC-WING-001:

```cypher
MATCH path = (n:Document {doc_id: 'SPEC-WING-001'})-[*1..2]-(m)
RETURN path
LIMIT 50
```

## Обслуживание

### Обновление данных

```python
builder = KnowledgeGraphBuilder()
builder.build_knowledge_graph()  # Пересоздаёт граф с нуля
```

### Частичное обновление

```python
# Добавить новый документ
with builder.driver.session() as session:
    session.run("""
        MERGE (d:Document {doc_id: $doc_id})
        SET d.title = $title, d.type = $type
    """, doc_id="NEW-DOC-001", title="Новый документ", type="specification")
```

### Резервное копирование

```bash
# Экспорт базы данных
neo4j-admin dump --database=neo4j --to=backup.dump

# Импорт базы данных
neo4j-admin load --from=backup.dump --database=neo4j --force
```

## Производительность

- Индексы создаются автоматически при построении графа
- Для больших баз рекомендуется использовать пакетную загрузку
- Кеширование результатов запросов на уровне приложения

## Troubleshooting

### Ошибка подключения к Neo4j

```
neo4j.exceptions.ServiceUnavailable: Unable to retrieve routing information
```

**Решение:** Проверьте, что Neo4j запущен и доступен на указанном URI.

### Медленные запросы

**Решение:** Убедитесь, что индексы созданы:

```cypher
SHOW INDEXES
```

### Конфликты версий

Граф автоматически отслеживает конфликты версий документов. Проверьте:

```python
conflicts = queries.find_conflicts()
```
