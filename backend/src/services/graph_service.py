from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from ..config import DATA_DIR
from ..utils.graph_builder import GraphBuilder
from ..models.schemas import GraphNode, GraphEdge

logger = logging.getLogger(__name__)


class GraphService:
    """Сервис для работы с графом связей документов"""
    
    def __init__(self):
        relations_file = DATA_DIR / "1_structured" / "relations.json"
        metadata_file = DATA_DIR / "1_structured" / "metadata.csv"
        self.graph_builder = GraphBuilder(
            relations_file=relations_file if relations_file.exists() else None,
            metadata_file=metadata_file if metadata_file.exists() else None
        )
    
    def get_document_graph(self, doc_id: str, depth: int = 2) -> Dict[str, Any]:
        """Получить граф связей для документа"""
        nodes, edges = self.graph_builder.get_document_graph(doc_id, depth)
        
        return {
            "nodes": [
                GraphNode(
                    id=node["id"],
                    type=node["type"],
                    label=node["label"],
                    metadata=node.get("metadata", {})
                )
                for node in nodes
            ],
            "edges": [
                GraphEdge(
                    source=edge["source"],
                    target=edge["target"],
                    relation=edge["relation"],
                    weight=edge.get("weight", 1.0)
                )
                for edge in edges
            ]
        }
    
    def find_related_documents(self, doc_id: str, max_results: int = 10) -> List[str]:
        """Найти связанные документы"""
        return self.graph_builder.find_related_documents(doc_id, max_results)
    
    def get_all_relations(self) -> Dict[str, Any]:
        """Получить все связи в графе"""
        nodes = []
        edges = []
        
        for node_id in self.graph_builder.graph.nodes():
            node_data = self.graph_builder.graph.nodes[node_id]
            metadata = self.graph_builder.metadata.get(node_id, {})
            nodes.append({
                "id": node_id,
                "type": node_data.get("type", "unknown"),
                "label": node_data.get("label", node_id),
                "metadata": metadata
            })
        
        for source, target, data in self.graph_builder.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "relation": data.get("relation", "связан с"),
                "weight": data.get("weight", 1.0)
            })
        
        return {
            "nodes": [
                GraphNode(
                    id=node["id"],
                    type=node["type"],
                    label=node["label"],
                    metadata=node.get("metadata", {})
                )
                for node in nodes
            ],
            "edges": [
                GraphEdge(
                    source=edge["source"],
                    target=edge["target"],
                    relation=edge["relation"],
                    weight=edge.get("weight", 1.0)
                )
                for edge in edges
            ]
        }

