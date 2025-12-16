"""API роуты для управления документами"""
from fastapi import APIRouter, HTTPException, status, File, UploadFile
from typing import List, Optional
import logging
from ..models.schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse,
    ErrorResponse
)
from ..services.document_service import DocumentService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def setup_document_routes(doc_service: DocumentService):
    """Установить роуты документов с сервисом"""
    
    @router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
    async def create_document(doc_data: DocumentCreate):
        """
        Создать новый документ
        
        Args:
            doc_data: Данные документа
            
        Returns:
            Информация о созданном документе
        """
        try:
            return await doc_service.create_document(doc_data)
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.get("/{doc_id}", response_model=DocumentResponse)
    async def get_document(doc_id: str):
        """
        Получить документ по ID
        
        Args:
            doc_id: ID документа
            
        Returns:
            Информация о документе
        """
        try:
            return await doc_service.get_document(doc_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @router.get("", response_model=List[DocumentResponse])
    async def get_all_documents():
        """
        Получить все документы
        
        Returns:
            Список документов
        """
        try:
            return await doc_service.get_all_documents()
        except Exception as e:
            logger.error(f"Error getting all documents: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @router.put("/{doc_id}", response_model=DocumentResponse)
    async def update_document(doc_id: str, update_data: DocumentUpdate):
        """
        Обновить документ
        
        Args:
            doc_id: ID документа
            update_data: Данные для обновления
            
        Returns:
            Обновленная информация о документе
        """
        try:
            return await doc_service.update_document(doc_id, update_data)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_document(doc_id: str):
        """
        Удалить документ
        
        Args:
            doc_id: ID документа
        """
        try:
            await doc_service.delete_document(doc_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @router.get("/stats/overview", response_model=dict)
    async def get_statistics():
        """
        Получить статистику по документам
        
        Returns:
            Статистика
        """
        try:
            return doc_service.get_statistics()
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    return router
