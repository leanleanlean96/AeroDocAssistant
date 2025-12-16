from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import logging

from ..models.schemas import UploadResponse
from ..services.document_service import DocumentService
from ..services.llm.main import RAGModel
from ..config import QDRANT_COLLECTION_NAME

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


def get_document_service() -> DocumentService:
    """Dependency для получения DocumentService"""
    rag_model = RAGModel(collection_name=QDRANT_COLLECTION_NAME)
    return DocumentService(rag_model)


@router.post("", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    service: DocumentService = Depends(get_document_service)
):
    """
    Загрузить и обработать документы
    """
    try:
        document_ids = []
        processed_count = 0
        
        for file in files:
            try:
                # Читаем содержимое файла
                content = await file.read()
                
                # Обрабатываем документ
                result = service.upload_file(content, file.filename)
                document_ids.append(result["doc_id"])
                processed_count += 1
                
                logger.info(f"Документ {file.filename} успешно загружен: {result['doc_id']}")
                
            except Exception as e:
                logger.error(f"Ошибка обработки файла {file.filename}: {e}")
                continue
        
        if processed_count == 0:
            raise HTTPException(status_code=400, detail="Не удалось обработать ни одного документа")
        
        return UploadResponse(
            success=True,
            message=f"Обработано документов: {processed_count}",
            documents_processed=processed_count,
            document_ids=document_ids
        )
        
    except Exception as e:
        logger.error(f"Ошибка загрузки документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dataset", response_model=UploadResponse)
async def upload_dataset(
    service: DocumentService = Depends(get_document_service)
):
    """
    Загрузить все документы из датасета
    """
    try:
        results = service.load_dataset_documents()
        
        if not results:
            raise HTTPException(status_code=404, detail="Документы в датасете не найдены")
        
        document_ids = [r["doc_id"] for r in results]
        
        return UploadResponse(
            success=True,
            message=f"Загружено документов из датасета: {len(results)}",
            documents_processed=len(results),
            document_ids=document_ids
        )
        
    except Exception as e:
        logger.error(f"Ошибка загрузки датасета: {e}")
        raise HTTPException(status_code=500, detail=str(e))

