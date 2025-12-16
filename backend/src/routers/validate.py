from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
import logging

from ..models.schemas import ValidationRequest, ValidationResponse
from ..services.validation_service import ValidationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/validate", tags=["validate"])


def get_validation_service() -> ValidationService:
    """Dependency для получения ValidationService"""
    return ValidationService()


@router.post("", response_model=ValidationResponse)
async def validate_documents(
    request: ValidationRequest,
    validation_service: ValidationService = Depends(get_validation_service)
):
    """
    Проверить документы на актуальность и противоречия
    """
    try:
        result = validation_service.validate_documents(request.document_ids)
        return ValidationResponse(**result)
    except Exception as e:
        logger.error(f"Ошибка валидации документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

