from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime
import logging

from ..models.schemas import AskRequest, AskResponse, Citation
from ..services.llm.main import RAGModel
from ..services.graph_service import GraphService
from ..services.validation_service import ValidationService
from ..config import QDRANT_COLLECTION_NAME

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ask", tags=["ask"])


def get_rag_model() -> RAGModel:
    """Dependency для получения RAGModel"""
    return RAGModel(collection_name=QDRANT_COLLECTION_NAME)


def get_graph_service() -> GraphService:
    """Dependency для получения GraphService"""
    return GraphService()


def get_validation_service() -> ValidationService:
    """Dependency для получения ValidationService"""
    return ValidationService()


@router.post("", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    rag_model: RAGModel = Depends(get_rag_model),
    graph_service: GraphService = Depends(get_graph_service),
    validation_service: ValidationService = Depends(get_validation_service)
):
    """
    Вопрос-ответ с цитированием источников и проверкой противоречий
    """
    try:
        # Получаем ответ с цитатами
        answer, citations_data = rag_model.ask(
            user_question=request.question,
            filter_docs=request.documents,
            max_context_tokens=request.max_context_tokens
        )
        
        # Формируем цитаты
        citations = [
            Citation(
                document_name=c.get("document_name", "Неизвестно"),
                chapter=c.get("chapter"),
                chunk_id=c.get("chunk_id"),
                text=c.get("text")
            )
            for c in citations_data
        ]
        
        # Получаем связанные документы из графа
        graph_links = []
        if citations:
            # Берем первый документ из цитат для поиска связей
            first_doc = citations[0].document_name
            try:
                related = graph_service.find_related_documents(first_doc, max_results=5)
                graph_links = related
            except:
                pass
        
        # Проверяем на противоречия
        contradictions = False
        freshness = None
        
        if citations:
            # Извлекаем ID документов из цитат
            doc_ids = list(set([c.document_name for c in citations]))
            
            # Проверяем противоречия
            conflicts = validation_service.check_contradictions(doc_ids)
            contradictions = len(conflicts) > 0
            
            # Получаем информацию о свежести
            freshness_info = validation_service.get_freshness_info(doc_ids)
            if freshness_info:
                # Находим самую свежую дату
                dates = []
                for doc_id, info in freshness_info.items():
                    if isinstance(info, dict):
                        issue_date = info.get("issue_date")
                        if issue_date and issue_date != "не указана":
                            dates.append(issue_date)
                if dates:
                    freshness = max(dates)
        
        return AskResponse(
            answer=answer,
            citations=citations,
            graph_links=graph_links,
            contradictions=contradictions,
            freshness=freshness
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки вопроса: {e}")
        raise HTTPException(status_code=500, detail=str(e))

