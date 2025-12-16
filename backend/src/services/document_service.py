"""Сервис управления документами"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..database.vector_db import VectorDatabase
from ..models.schemas import DocumentCreate, DocumentUpdate, DocumentResponse
from .embeddings_service import SberEmbeddingsService

logger = logging.getLogger(__name__)


class DocumentService:
    """Сервис для управления документами"""
    
    def __init__(self, vector_db: VectorDatabase, embeddings_service: SberEmbeddingsService):
        """
        Инициализация сервиса
        
        Args:
            vector_db: Экземпляр векторной БД
            embeddings_service: Сервис embeddings
        """
        self.vector_db = vector_db
        self.embeddings_service = embeddings_service
        self.documents_metadata = {}  # In-memory хранилище метаданных
    
    async def create_document(self, doc_data: DocumentCreate) -> DocumentResponse:
        """
        Создать новый документ
        
        Args:
            doc_data: Данные документа
            
        Returns:
            Информация о созданном документе
        """
        try:
            # Генерировать embedding для содержания
            embedding = await self.embeddings_service.get_embedding(doc_data.content)
            
            # Подготовить данные
            document_dict = doc_data.model_dump()
            
            # Добавить в БД
            doc_id = self.vector_db.add_document(document_dict, embedding)
            
            # Сохранить метаданные
            now = datetime.now()
            self.documents_metadata[doc_id] = {
                'id': doc_id,
                **document_dict,
                'created_at': now,
                'updated_at': now,
            }
            
            logger.info(f"Document created: {doc_id}")
            
            response_data = self.documents_metadata[doc_id]
            return DocumentResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            raise
    
    async def update_document(self, doc_id: str, update_data: DocumentUpdate) -> DocumentResponse:
        """
        Обновить документ
        
        Args:
            doc_id: ID документа
            update_data: Данные для обновления
            
        Returns:
            Обновленная информация о документе
        """
        try:
            # Получить текущий документ
            if doc_id not in self.documents_metadata:
                raise ValueError(f"Document not found: {doc_id}")
            
            current_doc = self.documents_metadata[doc_id]
            
            # Обновить данные
            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if value is not None:
                    current_doc[key] = value
            
            # Генерировать новый embedding (если изменилось содержание)
            if 'content' in update_dict:
                embedding = await self.embeddings_service.get_embedding(current_doc['content'])
            else:
                # Если содержание не изменилось, получить старый embedding
                # Для упрощения переиндексируем
                embedding = await self.embeddings_service.get_embedding(current_doc['content'])
            
            # Обновить в БД
            self.vector_db.update_document(doc_id, current_doc, embedding)
            
            # Обновить метаданные
            current_doc['updated_at'] = datetime.now()
            self.documents_metadata[doc_id] = current_doc
            
            logger.info(f"Document updated: {doc_id}")
            
            return DocumentResponse(**current_doc)
            
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            raise
    
    async def delete_document(self, doc_id: str):
        """
        Удалить документ
        
        Args:
            doc_id: ID документа
        """
        try:
            if doc_id not in self.documents_metadata:
                raise ValueError(f"Document not found: {doc_id}")
            
            self.vector_db.delete_document(doc_id)
            del self.documents_metadata[doc_id]
            
            logger.info(f"Document deleted: {doc_id}")
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise
    
    async def get_document(self, doc_id: str) -> DocumentResponse:
        """
        Получить документ по ID
        
        Args:
            doc_id: ID документа
            
        Returns:
            Информация о документе
        """
        try:
            if doc_id not in self.documents_metadata:
                raise ValueError(f"Document not found: {doc_id}")
            
            doc_data = self.documents_metadata[doc_id]
            return DocumentResponse(**doc_data)
            
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            raise
    
    async def get_all_documents(self) -> List[DocumentResponse]:
        """
        Получить все документы
        
        Returns:
            Список всех документов
        """
        try:
            documents = []
            for doc_id, doc_data in self.documents_metadata.items():
                documents.append(DocumentResponse(**doc_data))
            
            logger.info(f"Retrieved {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error getting all documents: {e}")
            raise
    
    async def search_documents(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Поиск документов по семантическому смыслу
        
        Args:
            query_text: Текст запроса
            top_k: Количество результатов
            
        Returns:
            Список найденных документов
        """
        try:
            # Генерировать embedding для запроса
            query_embedding = await self.embeddings_service.get_embedding(query_text)
            
            # Поиск в БД
            results = self.vector_db.search(query_embedding, top_k=top_k)
            
            logger.info(f"Search completed: found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику по документам
        
        Returns:
            Статистика
        """
        try:
            stats = self.vector_db.get_collection_stats()
            stats['documents_in_memory'] = len(self.documents_metadata)
            
            # Подсчитать документы по типам
            type_counts = {}
            for doc in self.documents_metadata.values():
                doc_type = doc.get('document_type', 'other')
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
            
            stats['documents_by_type'] = type_counts
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise
