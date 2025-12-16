"""
Модуль для построения графа знаний из документов авиационной технической документации.
Граф создается в Neo4j и содержит связи между спецификациями, стандартами, чертежами,
руководствами и другими документами.
"""

import json
import csv
import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from pathlib import Path

from neo4j import GraphDatabase
from dotenv import load_dotenv


load_dotenv("./env/neo4j.env")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


class KnowledgeGraphBuilder:
    """Класс для построения графа знаний в Neo4j"""
    
    def __init__(self, uri: str = NEO4J_URI, user: str = NEO4J_USER, password: str = NEO4J_PASSWORD):
        """
        Инициализация подключения к Neo4j
        
        Args:
            uri: URI базы данных Neo4j
            user: Имя пользователя
            password: Пароль
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.dataset_path = Path(__file__).parent.parent.parent.parent / "dataset"
        
    def close(self):
        """Закрытие соединения с базой данных"""
        self.driver.close()
        
    def clear_database(self):
        """Очистка базы данных перед загрузкой новых данных"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("База данных очищена")
            
    def create_indexes(self):
        """Создание индексов для оптимизации запросов"""
        with self.driver.session() as session:
            # Индексы для быстрого поиска по ID и типу
            session.run("CREATE INDEX doc_id_index IF NOT EXISTS FOR (d:Document) ON (d.doc_id)")
            session.run("CREATE INDEX doc_type_index IF NOT EXISTS FOR (d:Document) ON (d.type)")
            session.run("CREATE INDEX term_name_index IF NOT EXISTS FOR (t:Term) ON (t.term)")
            print("Индексы созданы")
            
    def load_metadata(self) -> List[Dict[str, Any]]:
        """
        Загрузка метаданных документов из CSV
        
        Returns:
            Список словарей с метаданными документов
        """
        metadata_path = self.dataset_path / "1_structured" / "metadata.csv"
        metadata = []
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                metadata.append(row)
                
        print(f"Загружено {len(metadata)} записей метаданных")
        return metadata
        
    def load_relations(self) -> Dict[str, Any]:
        """
        Загрузка связей между документами из JSON
        
        Returns:
            Словарь с узлами, рёбрами, конфликтами и устаревшими ссылками
        """
        relations_path = self.dataset_path / "1_structured" / "relations.json"
        
        with open(relations_path, 'r', encoding='utf-8') as f:
            relations = json.load(f)
            
        print(f"Загружено связей: узлов - {len(relations['graph_relations']['nodes'])}, "
              f"рёбер - {len(relations['graph_relations']['edges'])}")
        return relations
        
    def load_specifications(self) -> List[Dict[str, Any]]:
        """
        Загрузка подробных спецификаций из JSON-файлов
        
        Returns:
            Список словарей со спецификациями
        """
        specs_path = self.dataset_path / "1_structured" / "specifications"
        specifications = []
        
        for spec_file in specs_path.glob("*.json"):
            with open(spec_file, 'r', encoding='utf-8') as f:
                spec = json.load(f)
                specifications.append(spec)
                
        print(f"Загружено {len(specifications)} спецификаций")
        return specifications
        
    def load_standards(self) -> List[Dict[str, Any]]:
        """
        Загрузка стандартов из XML и JSON файлов
        
        Returns:
            Список словарей со стандартами
        """
        standards_path = self.dataset_path / "1_structured" / "standards"
        standards = []
        
        # Загрузка XML стандартов
        for std_file in standards_path.glob("*.xml"):
            try:
                tree = ET.parse(std_file)
                root = tree.getroot()
            except ET.ParseError as e:
                print(f"Предупреждение: не удалось разобрать {std_file.name}: {e}")
                continue
            
            standard = {
                'doc_id': root.find('id').text,
                'title': root.find('title').text,
                'type': root.find('type').text,
                'version': root.find('version').text,
                'status': root.find('status').text,
                'issue_date': root.find('issue_date').text,
                'sections': []
            }
            
            sections = root.find('sections')
            if sections is not None:
                for section in sections.findall('section'):
                    standard['sections'].append({
                        'num': section.find('num').text,
                        'title': section.find('title').text,
                        'content': section.find('content').text,
                        'page': section.find('page').text
                    })
                    
            standards.append(standard)
            
        # Загрузка JSON стандартов
        for std_file in standards_path.glob("*.json"):
            with open(std_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # JSON файлы имеют вложенную структуру с полем 'standard'
                if 'standard' in data:
                    standard = data['standard']
                    # Преобразуем 'id' в 'doc_id' для единообразия
                    standard['doc_id'] = standard.pop('id', standard.get('doc_id'))
                    standards.append(standard)
                else:
                    standards.append(data)
                
        print(f"Загружено {len(standards)} стандартов")
        return standards
        
    def load_glossary(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Загрузка глоссария терминов и аббревиатур
        
        Returns:
            Словарь с терминами и аббревиатурами
        """
        glossary_path = self.dataset_path / "3_glossary"
        
        # Загрузка терминов
        terms_path = glossary_path / "aviation_terms.json"
        with open(terms_path, 'r', encoding='utf-8') as f:
            terms = json.load(f)
            
        # Загрузка аббревиатур
        abbr_path = glossary_path / "abbreviations.csv"
        abbreviations = []
        with open(abbr_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                abbreviations.append(row)
                
        print(f"Загружено терминов: {len(terms)}, аббревиатур: {len(abbreviations)}")
        return {'terms': terms, 'abbreviations': abbreviations}
        
    def create_document_nodes(self, metadata: List[Dict[str, Any]]):
        """
        Создание узлов документов в графе
        
        Args:
            metadata: Список словарей с метаданными документов
        """
        with self.driver.session() as session:
            for doc in metadata:
                session.run("""
                    MERGE (d:Document {doc_id: $doc_id})
                    SET d.title = $title,
                        d.type = $type,
                        d.version = $version,
                        d.status = $status,
                        d.issue_date = $issue_date,
                        d.author = $author,
                        d.keywords = $keywords
                """, **doc)
                
        print(f"Создано {len(metadata)} узлов документов")
        
    def create_specification_details(self, specifications: List[Dict[str, Any]]):
        """
        Добавление детальной информации о спецификациях
        
        Args:
            specifications: Список словарей со спецификациями
        """
        with self.driver.session() as session:
            for spec in specifications:
                # Обновление основного узла документа
                session.run("""
                    MATCH (d:Document {doc_id: $doc_id})
                    SET d.sections_count = $sections_count
                """, doc_id=spec['doc_id'], sections_count=len(spec.get('sections', [])))
                
                # Создание узлов для секций
                for section in spec.get('sections', []):
                    session.run("""
                        MATCH (d:Document {doc_id: $doc_id})
                        MERGE (s:Section {section_id: $section_id, doc_id: $doc_id})
                        SET s.title = $title,
                            s.content = $content,
                            s.page = $page
                        MERGE (d)-[:HAS_SECTION]->(s)
                    """, doc_id=spec['doc_id'], **section)
                    
        print(f"Добавлены детали для {len(specifications)} спецификаций")
        
    def create_standard_details(self, standards: List[Dict[str, Any]]):
        """
        Добавление детальной информации о стандартах
        
        Args:
            standards: Список словарей со стандартами
        """
        with self.driver.session() as session:
            for std in standards:
                # Обновление основного узла документа
                session.run("""
                    MATCH (d:Document {doc_id: $doc_id})
                    SET d.sections_count = $sections_count
                """, doc_id=std['doc_id'], sections_count=len(std.get('sections', [])))
                
                # Создание узлов для секций
                for section in std.get('sections', []):
                    session.run("""
                        MATCH (d:Document {doc_id: $doc_id})
                        MERGE (s:Section {section_id: $num, doc_id: $doc_id})
                        SET s.title = $title,
                            s.content = $content,
                            s.page = $page
                        MERGE (d)-[:HAS_SECTION]->(s)
                    """, doc_id=std['doc_id'], 
                         num=section.get('num', section.get('section_id')),
                         title=section.get('title'),
                         content=section.get('content'),
                         page=section.get('page'))
                    
        print(f"Добавлены детали для {len(standards)} стандартов")
        
    def create_relationships(self, relations: Dict[str, Any]):
        """
        Создание связей между документами
        
        Args:
            relations: Словарь с информацией о связях
        """
        with self.driver.session() as session:
            # Создание основных связей
            for edge in relations['graph_relations']['edges']:
                session.run("""
                    MATCH (source:Document {doc_id: $source})
                    MATCH (target:Document {doc_id: $target})
                    MERGE (source)-[r:RELATES_TO {type: $relation}]->(target)
                """, **edge)
                
            # Создание узлов конфликтов
            for conflict in relations.get('conflicts', []):
                session.run("""
                    MATCH (doc1:Document {doc_id: $doc1})
                    MATCH (doc2:Document {doc_id: $doc2})
                    MERGE (c:Conflict {
                        id: $doc1 + '_' + $doc2,
                        type: $conflict_type,
                        description: $description,
                        severity: $severity
                    })
                    MERGE (doc1)-[:HAS_CONFLICT]->(c)
                    MERGE (doc2)-[:HAS_CONFLICT]->(c)
                """, **conflict)
                
            # Создание узлов устаревших ссылок
            for obsolete in relations.get('obsolete_links', []):
                session.run("""
                    MATCH (d:Document {doc_id: $document})
                    MERGE (o:ObsoleteReference {
                        id: $document + '_' + $obsolete_reference,
                        obsolete_reference: $obsolete_reference,
                        current_standard: $current_standard,
                        description: $description
                    })
                    MERGE (d)-[:HAS_OBSOLETE_REFERENCE]->(o)
                """, **obsolete)
                
        edges_count = len(relations['graph_relations']['edges'])
        conflicts_count = len(relations.get('conflicts', []))
        obsolete_count = len(relations.get('obsolete_links', []))
        
        print(f"Создано связей: {edges_count}, конфликтов: {conflicts_count}, "
              f"устаревших ссылок: {obsolete_count}")
        
    def create_glossary_nodes(self, glossary: Dict[str, List[Dict[str, Any]]]):
        """
        Создание узлов терминов и аббревиатур
        
        Args:
            glossary: Словарь с терминами и аббревиатурами
        """
        with self.driver.session() as session:
            # Создание терминов
            for term in glossary['terms']:
                session.run("""
                    MERGE (t:Term {term: $term})
                    SET t.definition = $definition,
                        t.en = $en,
                        t.category = $category,
                        t.examples = $examples
                """, 
                term=term['term'],
                definition=term['definition'],
                en=term.get('en', ''),
                category=term.get('category', ''),
                examples=','.join(term.get('examples', [])))
                
                # Связи с родственными терминами
                for related in term.get('related_terms', []):
                    session.run("""
                        MATCH (t1:Term {term: $term})
                        MERGE (t2:Term {term: $related})
                        MERGE (t1)-[:RELATED_TO]->(t2)
                    """, term=term['term'], related=related)
                    
            # Создание аббревиатур
            for abbr_data in glossary['abbreviations']:
                session.run("""
                    MERGE (a:Abbreviation {abbr: $abbreviation})
                    SET a.full_name = $full_name,
                        a.category = $category,
                        a.description = $description
                """, 
                abbreviation=abbr_data['abbreviation'],
                full_name=abbr_data['full_name'],
                category=abbr_data['category'],
                description=abbr_data['description'])
                
        print(f"Создано узлов: терминов - {len(glossary['terms'])}, "
              f"аббревиатур - {len(glossary['abbreviations'])}")
        
    def link_documents_to_terms(self, specifications: List[Dict[str, Any]], 
                               standards: List[Dict[str, Any]],
                               glossary: Dict[str, List[Dict[str, Any]]]):
        """
        Связывание документов с терминами на основе контента
        
        Args:
            specifications: Список спецификаций
            standards: Список стандартов
            glossary: Глоссарий терминов
        """
        terms_set = {term['term'].lower() for term in glossary['terms']}
        
        with self.driver.session() as session:
            # Связывание спецификаций с терминами
            for spec in specifications:
                for section in spec.get('sections', []):
                    content = section.get('content', '').lower()
                    for term in terms_set:
                        if term in content:
                            session.run("""
                                MATCH (d:Document {doc_id: $doc_id})
                                MATCH (t:Term {term: $term})
                                MERGE (d)-[:MENTIONS]->(t)
                            """, doc_id=spec['doc_id'], term=term)
                            
            # Связывание стандартов с терминами
            for std in standards:
                for section in std.get('sections', []):
                    content = section.get('content', '').lower()
                    for term in terms_set:
                        if term in content:
                            session.run("""
                                MATCH (d:Document {doc_id: $doc_id})
                                MATCH (t:Term {term: $term})
                                MERGE (d)-[:MENTIONS]->(t)
                            """, doc_id=std['doc_id'], term=term)
                            
        print("Документы связаны с терминами")
        
    def build_knowledge_graph(self):
        """
        Полная сборка графа знаний из всех источников данных
        """
        print("=" * 60)
        print("Начало построения графа знаний")
        print("=" * 60)
        
        # Очистка и подготовка базы данных
        self.clear_database()
        self.create_indexes()
        
        # Загрузка данных
        metadata = self.load_metadata()
        relations = self.load_relations()
        specifications = self.load_specifications()
        standards = self.load_standards()
        glossary = self.load_glossary()
        
        # Создание узлов и связей
        self.create_document_nodes(metadata)
        self.create_specification_details(specifications)
        self.create_standard_details(standards)
        self.create_relationships(relations)
        self.create_glossary_nodes(glossary)
        self.link_documents_to_terms(specifications, standards, glossary)
        
        print("=" * 60)
        print("Граф знаний успешно построен!")
        print("=" * 60)
        
    def get_statistics(self) -> Dict[str, int]:
        """
        Получение статистики по графу знаний
        
        Returns:
            Словарь со статистикой
        """
        with self.driver.session() as session:
            stats = {}
            
            # Подсчёт узлов по типам
            result = session.run("MATCH (d:Document) RETURN d.type as type, count(*) as count")
            stats['documents_by_type'] = {record['type']: record['count'] for record in result}
            
            # Общее количество узлов
            result = session.run("MATCH (n) RETURN count(n) as count")
            stats['total_nodes'] = result.single()['count']
            
            # Общее количество связей
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            stats['total_relationships'] = result.single()['count']
            
            # Количество конфликтов
            result = session.run("MATCH (c:Conflict) RETURN count(c) as count")
            stats['conflicts'] = result.single()['count']
            
            # Количество терминов
            result = session.run("MATCH (t:Term) RETURN count(t) as count")
            stats['terms'] = result.single()['count']
            
            return stats


def main():
    """Основная функция для запуска построения графа знаний"""
    builder = KnowledgeGraphBuilder()
    
    try:
        # Построение графа
        builder.build_knowledge_graph()
        
        # Вывод статистики
        print("\nСтатистика графа знаний:")
        stats = builder.get_statistics()
        print(f"Всего узлов: {stats['total_nodes']}")
        print(f"Всего связей: {stats['total_relationships']}")
        print(f"Конфликтов: {stats['conflicts']}")
        print(f"Терминов: {stats['terms']}")
        print("\nДокументы по типам:")
        for doc_type, count in stats['documents_by_type'].items():
            print(f"  {doc_type}: {count}")
            
    finally:
        builder.close()


if __name__ == "__main__":
    main()
