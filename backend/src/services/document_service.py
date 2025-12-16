import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4
import logging

from ..config import DATA_DIR, UPLOAD_DIR
from ..utils.document_parser import DocumentParser
from .llm.main import RAGModel

logger = logging.getLogger(__name__)


class DocumentService:
    """Сервис для работы с документами"""
    
    def __init__(self, rag_model: RAGModel):
        self.rag_model = rag_model
        self.parser = DocumentParser()
        self.processed_documents: Dict[str, Dict[str, Any]] = {}
    
    def process_document(self, file_path: Path, doc_id: Optional[str] = None) -> Dict[str, Any]:
        """Обработать документ и добавить в векторную БД"""
        if doc_id is None:
            doc_id = self._generate_doc_id(file_path)
        
        try:
            # Парсинг документа
            parsed = self.parser.parse_document(file_path)
            
            if "error" in parsed:
                raise Exception(parsed["error"])
            
            # Извлечение метаданных
            metadata = {
                "file_name": parsed["file_name"],
                "file_type": parsed["file_type"],
                "file_path": parsed["file_path"]
            }
            
            # Добавление чанков в векторную БД
            chunk_count = self.rag_model.add_document_chunks(
                text=parsed["text"],
                doc_id=doc_id,
                doc_name=parsed["file_name"],
                metadata=metadata
            )
            
            result = {
                "doc_id": doc_id,
                "file_name": parsed["file_name"],
                "file_type": parsed["file_type"],
                "chunks_added": chunk_count,
                "status": "success"
            }
            
            self.processed_documents[doc_id] = result
            logger.info(f"Документ {doc_id} обработан, добавлено {chunk_count} чанков")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка обработки документа {file_path}: {e}")
            raise
    
    def upload_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Загрузить файл и обработать"""
        # Сохраняем файл
        file_path = UPLOAD_DIR / filename
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Обрабатываем
        return self.process_document(file_path)
    
    def load_dataset_documents(self, dataset_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Загрузить все документы из датасета"""
        if dataset_path is None:
            dataset_path = DATA_DIR
        
        results = []
        
        # Структурированные документы
        structured_dir = dataset_path / "1_structured"
        if structured_dir.exists():
            # Спецификации
            specs_dir = structured_dir / "specifications"
            if specs_dir.exists():
                for json_file in specs_dir.glob("*.json"):
                    try:
                        result = self.process_document(json_file)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Ошибка обработки {json_file}: {e}")
            
            # Стандарты
            standards_dir = structured_dir / "standards"
            if standards_dir.exists():
                for std_file in standards_dir.glob("*"):
                    try:
                        result = self.process_document(std_file)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Ошибка обработки {std_file}: {e}")
        
        # Неструктурированные документы
        unstructured_dir = dataset_path / "2_unstructured"
        if unstructured_dir.exists():
            for subdir in ["drawings", "manuals", "reports", "tech_processes"]:
                subdir_path = unstructured_dir / subdir
                if subdir_path.exists():
                    for doc_file in subdir_path.glob("*"):
                        if doc_file.suffix.lower() in [".pdf", ".docx", ".doc"]:
                            try:
                                result = self.process_document(doc_file)
                                results.append(result)
                            except Exception as e:
                                logger.error(f"Ошибка обработки {doc_file}: {e}")
        
        logger.info(f"Загружено {len(results)} документов из датасета")
        return results
    
    def _generate_doc_id(self, file_path: Path) -> str:
        """Генерация ID документа на основе пути"""
        # Используем имя файла без расширения как основу
        base_name = file_path.stem
        # Добавляем хеш для уникальности
        path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
        return f"{base_name}-{path_hash}"
    
    def get_document_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о документе"""
        return self.processed_documents.get(doc_id)

