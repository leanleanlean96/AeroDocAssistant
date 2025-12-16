"""Pydantic модели для API"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Типы документов в авиационной отрасли"""
    ESKD = "eskd"  # Единая система конструкторской документации
    ESTD = "estd"  # Единая система технологической документации
    REPAIR_MANUAL = "repair_manual"  # Руководство по ремонту
    MATERIAL_CERT = "material_cert"  # Сертификат материала
    TEST_REPORT = "test_report"  # Отчет об испытаниях
    STANDARD = "standard"  # Отраслевой стандарт
    OTHER = "other"  # Прочее


class DocumentBase(BaseModel):
    """Базовая модель документа"""
    title: str = Field(..., description="Название документа")
    content: str = Field(..., description="Содержание документа")
    document_type: DocumentType = Field(default=DocumentType.OTHER, description="Тип документа")
    doc_number: Optional[str] = Field(default=None, description="Номер документа (ГОСТ, ESKD и т.д.)")
    version: str = Field(default="1.0", description="Версия документа")
    author: Optional[str] = Field(default=None, description="Автор документа")
    created_date: Optional[str] = Field(default=None, description="Дата создания")
    last_updated: Optional[str] = Field(default=None, description="Дата последнего обновления")
    tags: List[str] = Field(default_factory=list, description="Теги для поиска")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные метаданные")
    status: str = Field(default="active", description="Статус документа (active, archived, deprecated)")


class DocumentCreate(DocumentBase):
    """Модель для создания документа"""
    pass


class DocumentUpdate(BaseModel):
    """Модель для обновления документа"""
    title: Optional[str] = None
    content: Optional[str] = None
    document_type: Optional[DocumentType] = None
    doc_number: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class DocumentResponse(DocumentBase):
    """Ответ с информацией о документе"""
    id: str = Field(..., description="ID документа")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: datetime = Field(..., description="Время обновления")
    
    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    """Модель для поискового запроса"""
    query: str = Field(..., min_length=1, max_length=1000, description="Текст запроса")
    top_k: int = Field(default=5, ge=1, le=20, description="Количество результатов")
    document_types: Optional[List[DocumentType]] = Field(default=None, description="Фильтр по типам документов")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Дополнительные фильтры")


class SearchResult(BaseModel):
    """Результат поиска"""
    id: str = Field(..., description="ID документа")
    title: str = Field(..., description="Название документа")
    content_preview: str = Field(..., description="Предпросмотр содержания")
    relevance_score: float = Field(..., description="Оценка релевантности (0-1)")
    document_type: DocumentType = Field(..., description="Тип документа")
    doc_number: Optional[str] = None
    section: Optional[str] = Field(default=None, description="Раздел документа")
    page: Optional[int] = Field(default=None, description="Страница")
    match_positions: List[int] = Field(default_factory=list, description="Позиции совпадений")


class SearchResponse(BaseModel):
    """Ответ на поисковый запрос"""
    query: str = Field(..., description="Исходный запрос")
    total_results: int = Field(..., description="Общее количество результатов")
    results: List[SearchResult] = Field(..., description="Результаты поиска")
    execution_time_ms: float = Field(..., description="Время выполнения в миллисекундах")


class QARequest(BaseModel):
    """Запрос вопрос-ответ"""
    question: str = Field(..., min_length=1, max_length=2000, description="Вопрос")
    top_k_context: int = Field(default=5, ge=1, le=20, description="Количество контекстных документов")
    chat_history: Optional[List[Dict[str, str]]] = Field(default=None, description="История чата")


class QAResponse(BaseModel):
    """Ответ на вопрос с источниками"""
    question: str = Field(..., description="Исходный вопрос")
    answer: str = Field(..., description="Ответ")
    sources: List[Dict[str, Any]] = Field(..., description="Источники (документы)")
    confidence: float = Field(..., ge=0, le=1, description="Уверенность ответа")
    related_documents: List[SearchResult] = Field(default_factory=list, description="Связанные документы")


class DocumentLink(BaseModel):
    """Связь между документами"""
    source_doc_id: str = Field(..., description="ID исходного документа")
    target_doc_id: str = Field(..., description="ID целевого документа")
    link_type: str = Field(default="related", description="Тип связи (related, references, contradicts, updates)")
    confidence: float = Field(default=1.0, ge=0, le=1, description="Уверенность связи")
    description: Optional[str] = Field(default=None, description="Описание связи")


class GraphNode(BaseModel):
    """Узел графа документов"""
    id: str = Field(..., description="ID документа")
    title: str = Field(..., description="Название документа")
    document_type: DocumentType = Field(..., description="Тип документа")
    status: str = Field(..., description="Статус документа")


class GraphEdge(BaseModel):
    """Ребро графа документов"""
    source: str = Field(..., description="ID исходного документа")
    target: str = Field(..., description="ID целевого документа")
    link_type: str = Field(..., description="Тип связи")
    confidence: float = Field(..., description="Уверенность связи")


class KnowledgeGraph(BaseModel):
    """Граф знаний"""
    nodes: List[GraphNode] = Field(..., description="Узлы графа")
    edges: List[GraphEdge] = Field(..., description="Ребра графа")
    node_count: int = Field(..., description="Количество узлов")
    edge_count: int = Field(..., description="Количество ребер")


class ConsistencyCheckResult(BaseModel):
    """Результат проверки консистентности"""
    document_id: str = Field(..., description="ID проверяемого документа")
    issues: List[Dict[str, Any]] = Field(..., description="Найденные проблемы")
    warnings: List[Dict[str, Any]] = Field(..., description="Предупреждения")
    deprecated_references: List[Dict[str, Any]] = Field(..., description="Устаревшие ссылки")
    contradictions: List[Dict[str, Any]] = Field(..., description="Противоречия")


class ErrorResponse(BaseModel):
    """Модель ошибки"""
    status_code: int = Field(..., description="Код ошибки")
    message: str = Field(..., description="Сообщение об ошибке")
    detail: Optional[str] = Field(default=None, description="Подробности ошибки")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время ошибки")
