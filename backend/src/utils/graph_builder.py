import json
import networkx as nx
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Построитель графа связей между документами"""
    
    def __init__(self, relations_file: Optional[Path] = None, metadata_file: Optional[Path] = None):
        self.graph = nx.DiGraph()
        self.relations_file = relations_file
        self.metadata_file = metadata_file
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.conflicts: List[Dict[str, Any]] = []
        
        if relations_file and relations_file.exists():
            self._load_relations()
        
        if metadata_file and metadata_file.exists():
            self._load_metadata()
    
    def _load_relations(self):
        """Загрузка связей из relations.json"""
        try:
            with open(self.relations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            graph_data = data.get("graph_relations", {})
            
            # Добавляем узлы
            for node in graph_data.get("nodes", []):
                self.graph.add_node(
                    node["id"],
                    type=node.get("type", "unknown"),
                    label=node.get("label", node["id"])
                )
            
            # Добавляем рёбра
            for edge in graph_data.get("edges", []):
                self.graph.add_edge(
                    edge["source"],
                    edge["target"],
                    relation=edge.get("relation", "связан с"),
                    weight=1.0
                )
            
            # Сохраняем конфликты
            self.conflicts = data.get("conflicts", [])
            
            logger.info(f"Загружено {len(self.graph.nodes)} узлов и {len(self.graph.edges)} рёбер")
        except Exception as e:
            logger.error(f"Ошибка загрузки relations.json: {e}")
    
    def _load_metadata(self):
        """Загрузка метаданных из metadata.csv"""
        try:
            import csv
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    doc_id = row.get("doc_id")
                    if doc_id:
                        self.metadata[doc_id] = {
                            "title": row.get("title", ""),
                            "type": row.get("type", ""),
                            "version": row.get("version", ""),
                            "status": row.get("status", ""),
                            "issue_date": row.get("issue_date", ""),
                            "author": row.get("author", ""),
                            "keywords": row.get("keywords", "").split(",") if row.get("keywords") else []
                        }
            logger.info(f"Загружено метаданных для {len(self.metadata)} документов")
        except Exception as e:
            logger.error(f"Ошибка загрузки metadata.csv: {e}")
    
    def get_document_graph(self, doc_id: str, depth: int = 2) -> Tuple[List[Dict], List[Dict]]:
        """Получить граф связей для конкретного документа"""
        if doc_id not in self.graph:
            return [], []
        
        # Находим все связанные документы на заданной глубине
        nodes_to_include = {doc_id}
        current_level = {doc_id}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                # Предшественники и преемники
                predecessors = list(self.graph.predecessors(node))
                successors = list(self.graph.successors(node))
                next_level.update(predecessors)
                next_level.update(successors)
            nodes_to_include.update(next_level)
            current_level = next_level
        
        # Создаём подграф
        subgraph = self.graph.subgraph(nodes_to_include)
        
        # Формируем узлы
        nodes = []
        for node_id in subgraph.nodes():
            node_data = self.graph.nodes[node_id]
            metadata = self.metadata.get(node_id, {})
            nodes.append({
                "id": node_id,
                "type": node_data.get("type", "unknown"),
                "label": node_data.get("label", node_id),
                "metadata": metadata
            })
        
        # Формируем рёбра
        edges = []
        for source, target, data in subgraph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "relation": data.get("relation", "связан с"),
                "weight": data.get("weight", 1.0)
            })
        
        return nodes, edges
    
    def find_related_documents(self, doc_id: str, max_results: int = 10) -> List[str]:
        """Найти связанные документы"""
        if doc_id not in self.graph:
            return []
        
        related = set()
        # Прямые связи
        related.update(self.graph.predecessors(doc_id))
        related.update(self.graph.successors(doc_id))
        
        return list(related)[:max_results]
    
    def get_conflicts(self, doc_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Получить конфликты для указанных документов"""
        if doc_ids is None:
            return self.conflicts
        
        filtered_conflicts = []
        doc_set = set(doc_ids)
        for conflict in self.conflicts:
            if conflict.get("doc1") in doc_set or conflict.get("doc2") in doc_set:
                filtered_conflicts.append(conflict)
        
        return filtered_conflicts
    
    def check_freshness(self, doc_ids: Optional[List[str]] = None) -> Dict[str, str]:
        """Проверить актуальность документов по датам"""
        result = {}
        check_ids = doc_ids if doc_ids else list(self.metadata.keys())
        
        for doc_id in check_ids:
            if doc_id in self.metadata:
                issue_date = self.metadata[doc_id].get("issue_date")
                status = self.metadata[doc_id].get("status", "")
                result[doc_id] = {
                    "issue_date": issue_date or "не указана",
                    "status": status,
                    "is_obsolete": status.lower() in ["устаревший", "obsolete", "deprecated"]
                }
        
        return result

