"""Сервис управления графом знаний"""
import logging
from typing import List, Dict, Any, Set, Optional
import networkx as nx
import json
from datetime import datetime
from ..models.schemas import DocumentLink

logger = logging.getLogger(__name__)


class GraphService:
    """Сервис для работы с графом связей между документами"""
    
    def __init__(self):
        """Инициализация сервиса графа"""
        self.graph = nx.DiGraph()
        self.links = {}  # Хранилище связей между документами
    
    def add_document_to_graph(self, doc_id: str, doc_info: Dict[str, Any]):
        """
        Добавить документ в граф
        
        Args:
            doc_id: ID документа
            doc_info: Информация о документе
        """
        try:
            self.graph.add_node(
                doc_id,
                title=doc_info.get('title', 'Unknown'),
                document_type=doc_info.get('document_type', 'other'),
                version=doc_info.get('version', '1.0'),
                status=doc_info.get('status', 'active'),
            )
            logger.info(f"Document added to graph: {doc_id}")
        except Exception as e:
            logger.error(f"Error adding document to graph: {e}")
            raise
    
    def remove_document_from_graph(self, doc_id: str):
        """
        Удалить документ из графа
        
        Args:
            doc_id: ID документа
        """
        try:
            if doc_id in self.graph:
                self.graph.remove_node(doc_id)
                # Удалить все связи с этим документом
                if doc_id in self.links:
                    del self.links[doc_id]
                logger.info(f"Document removed from graph: {doc_id}")
        except Exception as e:
            logger.error(f"Error removing document from graph: {e}")
            raise
    
    def add_link(self, link: DocumentLink):
        """
        Добавить связь между документами
        
        Args:
            link: Информация о связи
        """
        try:
            # Убедиться, что оба документа в графе
            if link.source_doc_id not in self.graph or link.target_doc_id not in self.graph:
                logger.warning(f"One or both documents not in graph")
                return
            
            # Добавить ребро в граф
            self.graph.add_edge(
                link.source_doc_id,
                link.target_doc_id,
                link_type=link.link_type,
                confidence=link.confidence,
                description=link.description or ""
            )
            
            # Сохранить в хранилище
            if link.source_doc_id not in self.links:
                self.links[link.source_doc_id] = []
            
            self.links[link.source_doc_id].append({
                'target_doc_id': link.target_doc_id,
                'link_type': link.link_type,
                'confidence': link.confidence,
                'description': link.description,
                'created_at': datetime.now().isoformat()
            })
            
            logger.info(f"Link added: {link.source_doc_id} -> {link.target_doc_id}")
            
        except Exception as e:
            logger.error(f"Error adding link: {e}")
            raise
    
    def remove_link(self, source_doc_id: str, target_doc_id: str):
        """
        Удалить связь между документами
        
        Args:
            source_doc_id: ID исходного документа
            target_doc_id: ID целевого документа
        """
        try:
            if self.graph.has_edge(source_doc_id, target_doc_id):
                self.graph.remove_edge(source_doc_id, target_doc_id)
                
                # Удалить из хранилища
                if source_doc_id in self.links:
                    self.links[source_doc_id] = [
                        link for link in self.links[source_doc_id]
                        if link['target_doc_id'] != target_doc_id
                    ]
                
                logger.info(f"Link removed: {source_doc_id} -> {target_doc_id}")
        except Exception as e:
            logger.error(f"Error removing link: {e}")
            raise
    
    def get_graph_data(self) -> Dict[str, Any]:
        """
        Получить данные графа для визуализации
        
        Returns:
            Граф в формате для визуализации
        """
        try:
            nodes = []
            edges = []
            
            # Подготовить узлы
            for node_id, node_data in self.graph.nodes(data=True):
                nodes.append({
                    'id': node_id,
                    'label': node_data.get('title', node_id),
                    'type': node_data.get('document_type', 'other'),
                    'status': node_data.get('status', 'active'),
                })
            
            # Подготовить ребра
            for source, target, edge_data in self.graph.edges(data=True):
                edges.append({
                    'source': source,
                    'target': target,
                    'link_type': edge_data.get('link_type', 'related'),
                    'confidence': edge_data.get('confidence', 1.0),
                    'label': edge_data.get('link_type', 'related'),
                })
            
            return {
                'nodes': nodes,
                'edges': edges,
                'node_count': len(nodes),
                'edge_count': len(edges),
            }
            
        except Exception as e:
            logger.error(f"Error getting graph data: {e}")
            raise
    
    def find_related_documents(self, doc_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        Найти связанные документы
        
        Args:
            doc_id: ID документа
            max_depth: Максимальная глубина поиска
            
        Returns:
            Список связанных документов
        """
        try:
            related = []
            visited = set()
            
            def traverse(current_id: str, depth: int):
                if depth > max_depth or current_id in visited:
                    return
                
                visited.add(current_id)
                
                # Входящие связи
                for predecessor in self.graph.predecessors(current_id):
                    if predecessor not in visited:
                        edge_data = self.graph.get_edge_data(predecessor, current_id)
                        related.append({
                            'id': predecessor,
                            'title': self.graph.nodes[predecessor].get('title', 'Unknown'),
                            'link_type': edge_data.get('link_type', 'related'),
                            'confidence': edge_data.get('confidence', 1.0),
                            'direction': 'incoming',
                            'depth': depth + 1,
                        })
                        traverse(predecessor, depth + 1)
                
                # Исходящие связи
                for successor in self.graph.successors(current_id):
                    if successor not in visited:
                        edge_data = self.graph.get_edge_data(current_id, successor)
                        related.append({
                            'id': successor,
                            'title': self.graph.nodes[successor].get('title', 'Unknown'),
                            'link_type': edge_data.get('link_type', 'related'),
                            'confidence': edge_data.get('confidence', 1.0),
                            'direction': 'outgoing',
                            'depth': depth + 1,
                        })
                        traverse(successor, depth + 1)
            
            if doc_id in self.graph:
                traverse(doc_id, 0)
            
            return related
            
        except Exception as e:
            logger.error(f"Error finding related documents: {e}")
            raise
    
    def find_contradictions(self) -> List[Dict[str, Any]]:
        """
        Найти потенциальные противоречия в графе
        
        Returns:
            Список противоречий
        """
        try:
            contradictions = []
            
            # Поиск ребер типа 'contradicts'
            for source, target, edge_data in self.graph.edges(data=True):
                if edge_data.get('link_type') == 'contradicts':
                    source_data = self.graph.nodes[source]
                    target_data = self.graph.nodes[target]
                    
                    contradictions.append({
                        'source_doc_id': source,
                        'source_title': source_data.get('title'),
                        'target_doc_id': target,
                        'target_title': target_data.get('title'),
                        'confidence': edge_data.get('confidence', 1.0),
                        'description': edge_data.get('description', ''),
                    })
            
            return contradictions
            
        except Exception as e:
            logger.error(f"Error finding contradictions: {e}")
            raise
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику графа
        
        Returns:
            Статистика
        """
        try:
            stats = {
                'total_nodes': self.graph.number_of_nodes(),
                'total_edges': self.graph.number_of_edges(),
                'density': nx.density(self.graph),
            }
            
            # Подсчитать ребра по типам
            link_types = {}
            for source, target, edge_data in self.graph.edges(data=True):
                link_type = edge_data.get('link_type', 'related')
                link_types[link_type] = link_types.get(link_type, 0) + 1
            
            stats['link_types'] = link_types
            
            # Найти центральные узлы
            if self.graph.number_of_nodes() > 0:
                centrality = nx.degree_centrality(self.graph)
                top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
                stats['top_central_documents'] = [
                    {
                        'doc_id': doc_id,
                        'title': self.graph.nodes[doc_id].get('title', 'Unknown'),
                        'centrality': centrality_score
                    }
                    for doc_id, centrality_score in top_central
                ]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting graph statistics: {e}")
            raise
    
    def export_graph(self, format: str = 'json') -> str:
        """
        Экспортировать граф
        
        Args:
            format: Формат экспорта (json, gexf)
            
        Returns:
            Экспортированные данные
        """
        try:
            if format == 'json':
                graph_data = self.get_graph_data()
                return json.dumps(graph_data, ensure_ascii=False, indent=2)
            elif format == 'gexf':
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.gexf', delete=False) as f:
                    nx.write_gexf(self.graph, f.name)
                    with open(f.name, 'r') as gexf_file:
                        return gexf_file.read()
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting graph: {e}")
            raise
