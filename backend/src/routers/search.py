"""API роуты для поиска и RAG"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional, List
import logging
from ..models.schemas import SearchQuery, SearchResponse, SearchResult, QARequest, QAResponse
from ..services.document_service import DocumentService
from ..services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/search", tags=["search", "qa"])


def setup_search_routes(doc_service: DocumentService, rag_service: RAGService):
    """Установить роуты поиска и Q&A с сервисами"""
    
    @router.post("/semantic", response_model=SearchResponse)
    async def semantic_search(query_data: SearchQuery):
        """
        Семантический поиск по документам
        
        Args:
            query_data: Данные запроса
            
        Returns:
            Результаты поиска
        """
        try:
            import time
            start_time = time.time()
            
            # Выполнить поиск
            results = await doc_service.search_documents(
                query_data.query,
                top_k=query_data.top_k
            )
            
            # Преобразовать в SearchResult
            search_results = []
            for result in results:
                search_results.append(SearchResult(
                    id=result.get('id'),
                    title=result.get('title', 'Unknown'),
                    content_preview=result.get('content', '')[:500],
                    relevance_score=result.get('similarity', 0),
                    document_type=result.get('document_type', 'other'),
                    doc_number=result.get('doc_number'),
                    section=result.get('metadata', {}).get('section'),
                    page=result.get('metadata', {}).get('page'),
                ))
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            return SearchResponse(
                query=query_data.query,
                total_results=len(search_results),
                results=search_results,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.post("/qa", response_model=QAResponse)
    async def question_answer(qa_request: QARequest):
        """
        Ответить на вопрос с использованием RAG
        
        Args:
            qa_request: Запрос с вопросом
            
        Returns:
            Ответ с источниками
        """
        try:
            # Ответить на вопрос
            result = await rag_service.answer_question(
                question=qa_request.question,
                top_k=qa_request.top_k_context
            )
            
            # Преобразовать в QAResponse
            return QAResponse(
                question=result['question'],
                answer=result['answer'],
                sources=result['sources'],
                confidence=result['confidence'],
            )
            
        except Exception as e:
            logger.error(f"Error in Q&A: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get("/history/{session_id}", response_model=List[dict])
    async def get_conversation_history(session_id: str):
        """
        Получить историю беседы
        
        Args:
            session_id: ID сессии
            
        Returns:
            История диалога
        """
        try:
            return rag_service.get_conversation_history(session_id)
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.delete("/history/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def clear_conversation_history(session_id: str):
        """
        Очистить историю беседы
        
        Args:
            session_id: ID сессии
        """
        try:
            rag_service.clear_conversation_history(session_id)
        except Exception as e:
            logger.error(f"Error clearing conversation history: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    return router
