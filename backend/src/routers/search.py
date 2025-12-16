from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
import logging

from ..models.schemas import SearchRequest, SearchResponse, SearchResult, Citation
from ..services.llm.main import RAGModel
from ..config import QDRANT_COLLECTION_NAME, SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


def get_rag_model() -> RAGModel:
    """Dependency для получения RAGModel"""
    return RAGModel(collection_name=QDRANT_COLLECTION_NAME)


@router.post("", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    rag_model: RAGModel = Depends(get_rag_model)
):
    """
    Семантический поиск по документам
    """
    try:
        # Выполняем поиск
        search_results = rag_model.search(
            query=request.query,
            limit=request.limit,
            min_score=request.min_score
        )
        
        # Формируем результаты
        results = []
        for point, data in search_results:
            metadata = data["metadata"]
            citation = Citation(
                document_name=metadata.get("doc_name", metadata.get("doc_id", "Неизвестно")),
                chapter=metadata.get("doc_chapter", metadata.get("chapter")),
                chunk_id=str(point.id),
                text=data["content"][:200] + "..." if len(data["content"]) > 200 else data["content"]
            )
            
            results.append(
                SearchResult(
                    content=data["content"],
                    score=data["score"],
                    citation=citation,
                    metadata=metadata
                )
            )
        
        return SearchResponse(
            results=results,
            total=len(results)
        )
        
    except Exception as e:
        logger.error(f"Ошибка семантического поиска: {e}")
        raise HTTPException(status_code=500, detail=str(e))

