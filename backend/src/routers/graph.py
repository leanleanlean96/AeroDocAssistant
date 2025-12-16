"""API роуты для управления графом знаний"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
import logging
from ..models.schemas import DocumentLink, KnowledgeGraph, ConsistencyCheckResult
from ..services.graph_service import GraphService
from ..services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/graph", tags=["graph", "consistency"])


def setup_graph_routes(graph_service: GraphService, rag_service: RAGService):
    """Установить роуты графа с сервисом"""
    
    @router.get("", response_model=KnowledgeGraph)
    async def get_knowledge_graph():
        """
        Получить граф знаний
        
        Returns:
            Граф со всеми узлами и ребрами
        """
        try:
            graph_data = graph_service.get_graph_data()
            return KnowledgeGraph(**graph_data)
        except Exception as e:
            logger.error(f"Error getting knowledge graph: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.post("/links", status_code=status.HTTP_201_CREATED)
    async def add_link(link_data: DocumentLink):
        """
        Добавить связь между документами
        
        Args:
            link_data: Информация о связи
            
        Returns:
            Подтверждение добавления
        """
        try:
            graph_service.add_link(link_data)
            return {"status": "success", "message": "Link added successfully"}
        except Exception as e:
            logger.error(f"Error adding link: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.delete("/links/{source_doc_id}/{target_doc_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def remove_link(source_doc_id: str, target_doc_id: str):
        """
        Удалить связь между документами
        
        Args:
            source_doc_id: ID исходного документа
            target_doc_id: ID целевого документа
        """
        try:
            graph_service.remove_link(source_doc_id, target_doc_id)
        except Exception as e:
            logger.error(f"Error removing link: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get("/related/{doc_id}", response_model=List[dict])
    async def get_related_documents(doc_id: str, max_depth: int = 2):
        """
        Получить связанные документы
        
        Args:
            doc_id: ID документа
            max_depth: Максимальная глубина поиска
            
        Returns:
            Список связанных документов
        """
        try:
            return graph_service.find_related_documents(doc_id, max_depth=max_depth)
        except Exception as e:
            logger.error(f"Error getting related documents: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get("/contradictions", response_model=List[dict])
    async def find_contradictions():
        """
        Найти потенциальные противоречия в графе
        
        Returns:
            Список противоречий
        """
        try:
            return graph_service.find_contradictions()
        except Exception as e:
            logger.error(f"Error finding contradictions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get("/statistics", response_model=dict)
    async def get_graph_statistics():
        """
        Получить статистику графа
        
        Returns:
            Статистика
        """
        try:
            return graph_service.get_graph_statistics()
        except Exception as e:
            logger.error(f"Error getting graph statistics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get("/export", response_model=dict)
    async def export_graph(format: str = "json"):
        """
        Экспортировать граф
        
        Args:
            format: Формат экспорта (json, gexf)
            
        Returns:
            Экспортированные данные
        """
        try:
            data = graph_service.export_graph(format=format)
            return {"format": format, "data": data}
        except Exception as e:
            logger.error(f"Error exporting graph: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.post("/consistency/{doc_id}", response_model=ConsistencyCheckResult)
    async def check_consistency(doc_id: str):
        """
        Проверить консистентность документа
        
        Args:
            doc_id: ID документа
            
        Returns:
            Результаты проверки
        """
        try:
            return await rag_service.check_consistency(doc_id)
        except Exception as e:
            logger.error(f"Error checking consistency: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    return router
