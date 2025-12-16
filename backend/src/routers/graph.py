from fastapi import APIRouter, HTTPException, Depends, Path
from typing import Optional
import logging

from ..models.schemas import GraphResponse
from ..services.graph_service import GraphService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])


def get_graph_service() -> GraphService:
    """Dependency для получения GraphService"""
    return GraphService()


@router.get("/{doc_id}", response_model=GraphResponse)
async def get_document_graph(
    doc_id: str = Path(..., description="ID документа"),
    depth: int = 2,
    graph_service: GraphService = Depends(get_graph_service)
):
    """
    Получить граф связей для конкретного документа
    """
    try:
        graph_data = graph_service.get_document_graph(doc_id, depth=depth)
        return GraphResponse(**graph_data)
    except Exception as e:
        logger.error(f"Ошибка получения графа для {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=GraphResponse)
async def get_all_graph(
    graph_service: GraphService = Depends(get_graph_service)
):
    """
    Получить весь граф связей между документами
    """
    try:
        graph_data = graph_service.get_all_relations()
        return GraphResponse(**graph_data)
    except Exception as e:
        logger.error(f"Ошибка получения полного графа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

