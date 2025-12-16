from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..config import DATA_DIR
from ..utils.graph_builder import GraphBuilder
from ..models.schemas import DocumentInfo, Conflict

logger = logging.getLogger(__name__)


class ValidationService:
    """Сервис для проверки актуальности и противоречий"""
    
    def __init__(self):
        relations_file = DATA_DIR / "1_structured" / "relations.json"
        metadata_file = DATA_DIR / "1_structured" / "metadata.csv"
        self.graph_builder = GraphBuilder(
            relations_file=relations_file if relations_file.exists() else None,
            metadata_file=metadata_file if metadata_file.exists() else None
        )
    
    def validate_documents(self, doc_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Проверить документы на актуальность и противоречия"""
        # Проверка актуальности
        freshness_check = self.graph_builder.check_freshness(doc_ids)
        
        # Поиск устаревших документов
        obsolete_documents = []
        for doc_id, info in freshness_check.items():
            if isinstance(info, dict) and info.get("is_obsolete"):
                metadata = self.graph_builder.metadata.get(doc_id, {})
                obsolete_documents.append(
                    DocumentInfo(
                        doc_id=doc_id,
                        title=metadata.get("title", doc_id),
                        type=metadata.get("type", "unknown"),
                        version=metadata.get("version"),
                        status=metadata.get("status"),
                        issue_date=metadata.get("issue_date")
                    )
                )
        
        # Поиск конфликтов
        conflicts_data = self.graph_builder.get_conflicts(doc_ids)
        conflicts = [
            Conflict(
                doc1=conflict.get("doc1", ""),
                doc2=conflict.get("doc2", ""),
                conflict_type=conflict.get("conflict_type", "неизвестный"),
                description=conflict.get("description", ""),
                severity=conflict.get("severity", "средняя")
            )
            for conflict in conflicts_data
        ]
        
        # Поиск устаревших ссылок
        outdated_references = []
        if hasattr(self.graph_builder, 'graph') and doc_ids:
            # Проверяем связи на устаревшие стандарты
            for doc_id in doc_ids:
                if doc_id in self.graph_builder.graph:
                    for target in self.graph_builder.graph.successors(doc_id):
                        target_metadata = self.graph_builder.metadata.get(target, {})
                        if target_metadata.get("status", "").lower() in ["устаревший", "obsolete"]:
                            outdated_references.append({
                                "document": doc_id,
                                "obsolete_reference": target,
                                "description": f"Документ ссылается на устаревший стандарт {target}"
                            })
        
        return {
            "obsolete_documents": obsolete_documents,
            "conflicts": conflicts,
            "outdated_references": outdated_references,
            "freshness_check": freshness_check
        }
    
    def check_contradictions(self, doc_ids: List[str]) -> List[Conflict]:
        """Проверить противоречия между документами"""
        conflicts_data = self.graph_builder.get_conflicts(doc_ids)
        return [
            Conflict(
                doc1=conflict.get("doc1", ""),
                doc2=conflict.get("doc2", ""),
                conflict_type=conflict.get("conflict_type", "неизвестный"),
                description=conflict.get("description", ""),
                severity=conflict.get("severity", "средняя")
            )
            for conflict in conflicts_data
        ]
    
    def get_freshness_info(self, doc_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Получить информацию об актуальности документов"""
        return self.graph_builder.check_freshness(doc_ids)

