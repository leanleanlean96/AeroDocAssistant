from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Citation(BaseModel):
    """Цитата из документа"""
    document_name: str = Field(..., description="Название документа")
    chapter: Optional[str] = Field(None, description="Раздел/глава")
    page: Optional[str] = Field(None, description="Страница")
    chunk_id: Optional[str] = Field(None, description="ID чанка")
    text: Optional[str] = Field(None, description="Текст цитаты")


class DocumentInfo(BaseModel):
    """Информация о документе"""
    doc_id: str
    title: str
    type: str
    version: Optional[str] = None
    status: Optional[str] = None
    issue_date: Optional[str] = None


class UploadResponse(BaseModel):
    """Ответ на загрузку документов"""
    success: bool
    message: str
    documents_processed: int
    document_ids: List[str]


class SearchRequest(BaseModel):
    """Запрос на семантический поиск"""
    query: str = Field(..., description="Поисковый запрос")
    limit: int = Field(10, ge=1, le=50, description="Количество результатов")
    min_score: float = Field(0.65, ge=0.0, le=1.0, description="Минимальный score")


class SearchResult(BaseModel):
    """Результат поиска"""
    content: str
    score: float
    citation: Citation
    metadata: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Ответ на поисковый запрос"""
    results: List[SearchResult]
    total: int


class AskRequest(BaseModel):
    """Запрос на вопрос-ответ"""
    question: str = Field(..., description="Вопрос пользователя")
    documents: Optional[List[str]] = Field(None, description="Список ID документов для ограничения поиска")
    max_context_tokens: int = Field(1000, ge=100, le=4000)


class AskResponse(BaseModel):
    """Ответ на вопрос"""
    answer: str
    citations: List[Citation]
    graph_links: List[str] = Field(default_factory=list, description="ID связанных документов")
    contradictions: bool = Field(False, description="Есть ли противоречия")
    freshness: Optional[str] = Field(None, description="Дата самого свежего документа")


class GraphNode(BaseModel):
    """Узел графа"""
    id: str
    type: str
    label: str
    metadata: Optional[Dict[str, Any]] = None


class GraphEdge(BaseModel):
    """Ребро графа"""
    source: str
    target: str
    relation: str
    weight: Optional[float] = None


class GraphResponse(BaseModel):
    """Граф связей документов"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class Conflict(BaseModel):
    """Противоречие между документами"""
    doc1: str
    doc2: str
    conflict_type: str
    description: str
    severity: str


class ValidationRequest(BaseModel):
    """Запрос на проверку актуальности и противоречий"""
    document_ids: Optional[List[str]] = Field(None, description="ID документов для проверки. Если None - проверяются все")


class ValidationResponse(BaseModel):
    """Результат проверки"""
    obsolete_documents: List[DocumentInfo]
    conflicts: List[Conflict]
    outdated_references: List[Dict[str, Any]]
    freshness_check: Dict[str, str] = Field(default_factory=dict, description="Даты документов")

