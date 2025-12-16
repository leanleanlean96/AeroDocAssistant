"""Работа с векторной базой данных Chroma"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class VectorDatabase:
    """Управление векторной БД для хранения документов и embeddings"""
    
    def __init__(self, db_path: str):
        """
        Инициализация векторной БД
        
        Args:
            db_path: Путь к директории БД Chroma
        """
        self.db_path = db_path
        
        # Настройка Chroma
        try:
            chroma_settings = ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=db_path,
                anonymized_telemetry=False,
            )

            # Попытка использовать явную конфигурацию (новые версии Chroma могут
            # выдавать предупреждение/исключение при устаревшей конфигурации).
            self.client = chromadb.Client(chroma_settings)
            self.collection = self.client.get_or_create_collection(
                name="aviation_documents",
                metadata={"hnsw:space": "cosine"}
            )

        except Exception as e:
            # Если текущая конфигурация устарела (или возникла любая другая
            # ошибка при инициализации клиента), логируем и откатываемся к
            # клиенту по умолчанию (in-memory или системному), чтобы приложение
            # могло запуститься. Это временное решение для разработки.
            logger.warning(f"Chroma client init failed, falling back to default client: {e}")
            self.client = chromadb.Client()
            # В некоторых окружениях get_or_create_collection принимает
            # только имя; метаданные добавим при возможности.
            try:
                self.collection = self.client.get_or_create_collection(name="aviation_documents")
            except Exception:
                # Если и это не сработало, попробуем создать коллекцию явно
                self.collection = self.client.create_collection(name="aviation_documents")
        
    def add_document(self, document: Dict[str, Any], embedding: List[float]) -> str:
        """
        Добавить документ с embedding
        
        Args:
            document: Информация о документе
            embedding: Вектор embedding
            
        Returns:
            ID документа
        """
        doc_id = str(uuid.uuid4())
        
        # Подготовка данных
        doc_copy = document.copy()
        doc_copy['id'] = doc_id
        doc_copy['created_at'] = datetime.now().isoformat()
        
        try:
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[document.get('content', '')],
                metadatas=[{
                    'title': document.get('title', ''),
                    'document_type': document.get('document_type', 'other'),
                    'doc_number': document.get('doc_number', ''),
                    'version': document.get('version', '1.0'),
                    'author': document.get('author', ''),
                    'status': document.get('status', 'active'),
                    'tags': json.dumps(document.get('tags', [])),
                    'metadata': json.dumps(document.get('metadata', {})),
                    'created_at': doc_copy['created_at'],
                }]
            )
            logger.info(f"Document added: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    def update_document(self, doc_id: str, document: Dict[str, Any], embedding: List[float]):
        """
        Обновить документ
        
        Args:
            doc_id: ID документа
            document: Обновленная информация
            embedding: Новый embedding
        """
        try:
            # Удалить старый документ
            self.collection.delete(ids=[doc_id])
            
            # Добавить обновленный
            document_copy = document.copy()
            document_copy['id'] = doc_id
            document_copy['updated_at'] = datetime.now().isoformat()
            
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[document.get('content', '')],
                metadatas=[{
                    'title': document.get('title', ''),
                    'document_type': document.get('document_type', 'other'),
                    'doc_number': document.get('doc_number', ''),
                    'version': document.get('version', '1.0'),
                    'author': document.get('author', ''),
                    'status': document.get('status', 'active'),
                    'tags': json.dumps(document.get('tags', [])),
                    'metadata': json.dumps(document.get('metadata', {})),
                    'updated_at': document_copy['updated_at'],
                }]
            )
            logger.info(f"Document updated: {doc_id}")
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            raise
    
    def delete_document(self, doc_id: str):
        """
        Удалить документ
        
        Args:
            doc_id: ID документа
        """
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Document deleted: {doc_id}")
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise
    
    def search(self, embedding: List[float], top_k: int = 5, 
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Поиск по embedding
        
        Args:
            embedding: Вектор для поиска
            top_k: Количество результатов
            filters: Фильтры по метаданным
            
        Returns:
            Список найденных документов
        """
        try:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where=filters
            )
            
            documents = []
            if results['ids'] and len(results['ids']) > 0:
                for i, doc_id in enumerate(results['ids'][0]):
                    doc_data = {
                        'id': doc_id,
                        'content': results['documents'][0][i] if results['documents'][0] else '',
                        'distance': results['distances'][0][i] if results['distances'] else 1.0,
                        'similarity': 1 - (results['distances'][0][i] if results['distances'] else 1.0),
                    }
                    
                    # Добавить метаданные
                    if results['metadatas'] and results['metadatas'][0]:
                        metadata = results['metadatas'][0][i]
                        doc_data.update(metadata)
                        
                        # Распарсить JSON поля
                        if 'tags' in metadata:
                            try:
                                doc_data['tags'] = json.loads(metadata['tags'])
                            except:
                                doc_data['tags'] = []
                        if 'metadata' in metadata:
                            try:
                                doc_data['metadata'] = json.loads(metadata['metadata'])
                            except:
                                doc_data['metadata'] = {}
                    
                    documents.append(doc_data)
            
            return documents
        except Exception as e:
            logger.error(f"Error searching: {e}")
            raise
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить документ по ID
        
        Args:
            doc_id: ID документа
            
        Returns:
            Информация о документе или None
        """
        try:
            results = self.collection.get(ids=[doc_id])
            
            if not results['ids']:
                return None
            
            doc_data = {
                'id': doc_id,
                'content': results['documents'][0] if results['documents'] else '',
            }
            
            if results['metadatas'] and results['metadatas'][0]:
                metadata = results['metadatas'][0]
                doc_data.update(metadata)
                
                # Распарсить JSON поля
                if 'tags' in metadata:
                    try:
                        doc_data['tags'] = json.loads(metadata['tags'])
                    except:
                        doc_data['tags'] = []
                if 'metadata' in metadata:
                    try:
                        doc_data['metadata'] = json.loads(metadata['metadata'])
                    except:
                        doc_data['metadata'] = {}
            
            return doc_data
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            raise
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Получить все документы
        
        Returns:
            Список всех документов
        """
        try:
            results = self.collection.get()
            
            documents = []
            if results['ids']:
                for i, doc_id in enumerate(results['ids']):
                    doc_data = {
                        'id': doc_id,
                        'content': results['documents'][i] if results['documents'] else '',
                    }
                    
                    if results['metadatas'] and results['metadatas'][i]:
                        metadata = results['metadatas'][i]
                        doc_data.update(metadata)
                        
                        if 'tags' in metadata:
                            try:
                                doc_data['tags'] = json.loads(metadata['tags'])
                            except:
                                doc_data['tags'] = []
                        if 'metadata' in metadata:
                            try:
                                doc_data['metadata'] = json.loads(metadata['metadata'])
                            except:
                                doc_data['metadata'] = {}
                    
                    documents.append(doc_data)
            
            return documents
        except Exception as e:
            logger.error(f"Error getting all documents: {e}")
            raise
    
    def delete_all(self):
        """Удалить все документы из коллекции"""
        try:
            # Получить все документы
            results = self.collection.get()
            if results['ids']:
                self.collection.delete(ids=results['ids'])
            logger.info("All documents deleted")
        except Exception as e:
            logger.error(f"Error deleting all documents: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Получить статистику коллекции
        
        Returns:
            Статистика коллекции
        """
        try:
            results = self.collection.get()
            return {
                'total_documents': len(results['ids']) if results['ids'] else 0,
                'collection_name': self.collection.name,
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            raise
