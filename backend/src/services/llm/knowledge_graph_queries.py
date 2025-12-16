"""
Примеры запросов к графу знаний для различных сценариев использования
"""

from .knowledge_graph import KnowledgeGraphBuilder


class KnowledgeGraphQueries:
    """Класс для выполнения запросов к графу знаний"""
    
    def __init__(self):
        self.builder = KnowledgeGraphBuilder()
        
    def close(self):
        """Закрытие соединения"""
        self.builder.close()
        
    def find_document_by_id(self, doc_id: str):
        """Найти документ по ID"""
        with self.builder.driver.session() as session:
            result = session.run("""
                MATCH (d:Document {doc_id: $doc_id})
                RETURN d
            """, doc_id=doc_id)
            return result.single()
            
    def find_related_documents(self, doc_id: str, max_depth: int = 2):
        """
        Найти все документы, связанные с данным документом
        
        Args:
            doc_id: ID документа
            max_depth: Максимальная глубина связей
        """
        with self.builder.driver.session() as session:
            result = session.run("""
                MATCH path = (d:Document {doc_id: $doc_id})-[r:RELATES_TO*1..""" + str(max_depth) + """]->(related:Document)
                RETURN DISTINCT related.doc_id as doc_id, 
                       related.title as title, 
                       related.type as type,
                       length(path) as distance
                ORDER BY distance, related.type
            """, doc_id=doc_id)
            return [dict(record) for record in result]
            
    def find_conflicts(self):
        """Найти все конфликты в документации"""
        with self.builder.driver.session() as session:
            result = session.run("""
                MATCH (d1:Document)-[:HAS_CONFLICT]->(c:Conflict)<-[:HAS_CONFLICT]-(d2:Document)
                RETURN d1.doc_id as doc1_id,
                       d1.title as doc1_title,
                       d2.doc_id as doc2_id,
                       d2.title as doc2_title,
                       c.type as conflict_type,
                       c.description as description,
                       c.severity as severity
                ORDER BY c.severity DESC
            """)
            return [dict(record) for record in result]
            
    def find_obsolete_references(self):
        """Найти все устаревшие ссылки"""
        with self.builder.driver.session() as session:
            result = session.run("""
                MATCH (d:Document)-[:HAS_OBSOLETE_REFERENCE]->(o:ObsoleteReference)
                RETURN d.doc_id as doc_id,
                       d.title as title,
                       o.obsolete_reference as obsolete_ref,
                       o.current_standard as current_std,
                       o.description as description
            """)
            return [dict(record) for record in result]
            
    def find_documents_by_term(self, term: str):
        """
        Найти все документы, которые упоминают данный термин
        
        Args:
            term: Термин для поиска
        """
        with self.builder.driver.session() as session:
            result = session.run("""
                MATCH (d:Document)-[:MENTIONS]->(t:Term {term: $term})
                RETURN d.doc_id as doc_id,
                       d.title as title,
                       d.type as type
                ORDER BY d.type, d.title
            """, term=term)
            return [dict(record) for record in result]
            
    def find_standards_for_specification(self, spec_id: str):
        """
        Найти все стандарты, на которые ссылается спецификация
        
        Args:
            spec_id: ID спецификации
        """
        with self.builder.driver.session() as session:
            result = session.run("""
                MATCH (spec:Document {doc_id: $spec_id, type: 'specification'})
                      -[:RELATES_TO]->(std:Document {type: 'standard'})
                RETURN std.doc_id as std_id,
                       std.title as title,
                       std.status as status,
                       std.version as version
                ORDER BY std.title
            """, spec_id=spec_id)
            return [dict(record) for record in result]
            
    def find_specification_dependencies(self, spec_id: str):
        """
        Найти все зависимости спецификации (стандарты, чертежи, руководства)
        
        Args:
            spec_id: ID спецификации
        """
        with self.builder.driver.session() as session:
            result = session.run("""
                MATCH (spec:Document {doc_id: $spec_id})-[r:RELATES_TO]->(dep:Document)
                RETURN dep.doc_id as doc_id,
                       dep.title as title,
                       dep.type as type,
                       r.type as relation_type
                ORDER BY dep.type, dep.title
            """, spec_id=spec_id)
            return [dict(record) for record in result]
            
    def find_documents_by_keyword(self, keyword: str):
        """
        Найти документы по ключевому слову
        
        Args:
            keyword: Ключевое слово для поиска
        """
        with self.builder.driver.session() as session:
            result = session.run("""
                MATCH (d:Document)
                WHERE d.keywords CONTAINS $keyword
                RETURN d.doc_id as doc_id,
                       d.title as title,
                       d.type as type,
                       d.keywords as keywords
                ORDER BY d.type, d.title
            """, keyword=keyword)
            return [dict(record) for record in result]
            
    def find_outdated_documents(self):
        """Найти все устаревшие документы"""
        with self.builder.driver.session() as session:
            result = session.run("""
                MATCH (d:Document {status: 'устаревший'})
                RETURN d.doc_id as doc_id,
                       d.title as title,
                       d.type as type,
                       d.version as version,
                       d.issue_date as issue_date
                ORDER BY d.issue_date DESC
            """)
            return [dict(record) for record in result]
            
    def find_replacement_chain(self, old_doc_id: str):
        """
        Найти цепочку замены документа (что заменяет что)
        
        Args:
            old_doc_id: ID устаревшего документа
        """
        with self.builder.driver.session() as session:
            result = session.run("""
                MATCH path = (old:Document {doc_id: $old_doc_id})
                             <-[:RELATES_TO*]-(new:Document)
                WHERE any(r in relationships(path) WHERE r.type = 'заменён' OR r.type = 'устарел, заменён на')
                RETURN new.doc_id as doc_id,
                       new.title as title,
                       new.type as type,
                       new.status as status,
                       length(path) as steps
                ORDER BY steps
            """, old_doc_id=old_doc_id)
            return [dict(record) for record in result]
            
    def get_document_impact_analysis(self, doc_id: str):
        """
        Анализ влияния документа - какие документы зависят от данного
        
        Args:
            doc_id: ID документа
        """
        with self.builder.driver.session() as session:
            result = session.run("""
                MATCH (source:Document)-[:RELATES_TO]->(target:Document {doc_id: $doc_id})
                RETURN source.doc_id as dependent_doc_id,
                       source.title as dependent_title,
                       source.type as dependent_type,
                       source.status as dependent_status
                ORDER BY source.type, source.title
            """, doc_id=doc_id)
            return [dict(record) for record in result]
            
    def find_term_definition(self, term: str):
        """
        Найти определение термина и связанные термины
        
        Args:
            term: Термин для поиска
        """
        with self.builder.driver.session() as session:
            result = session.run("""
                MATCH (t:Term {term: $term})
                OPTIONAL MATCH (t)-[:RELATED_TO]->(related:Term)
                RETURN t.term as term,
                       t.definition as definition,
                       t.en as english,
                       t.category as category,
                       t.examples as examples,
                       collect(DISTINCT related.term) as related_terms
            """, term=term)
            return result.single()
            
    def search_documents_by_content(self, search_text: str):
        """
        Поиск документов по содержимому секций
        
        Args:
            search_text: Текст для поиска
        """
        with self.builder.driver.session() as session:
            result = session.run("""
                MATCH (d:Document)-[:HAS_SECTION]->(s:Section)
                WHERE toLower(s.content) CONTAINS toLower($search_text)
                   OR toLower(s.title) CONTAINS toLower($search_text)
                RETURN DISTINCT d.doc_id as doc_id,
                       d.title as doc_title,
                       d.type as doc_type,
                       s.section_id as section_id,
                       s.title as section_title,
                       s.page as page
                ORDER BY d.type, d.title, s.section_id
            """, search_text=search_text)
            return [dict(record) for record in result]
            

def demo_queries():
    """Демонстрация различных запросов к графу знаний"""
    queries = KnowledgeGraphQueries()
    
    try:
        print("=" * 60)
        print("ДЕМОНСТРАЦИЯ ЗАПРОСОВ К ГРАФУ ЗНАНИЙ")
        print("=" * 60)
        
        # 1. Найти связанные документы
        print("\n1. Документы, связанные с SPEC-WING-001:")
        related = queries.find_related_documents("SPEC-WING-001")
        for doc in related[:5]:  # Показать первые 5
            print(f"   - {doc['doc_id']}: {doc['title']} (расстояние: {doc['distance']})")
            
        # 2. Найти конфликты
        print("\n2. Конфликты в документации:")
        conflicts = queries.find_conflicts()
        for conflict in conflicts:
            print(f"   - {conflict['doc1_id']} ↔ {conflict['doc2_id']}")
            print(f"     Тип: {conflict['conflict_type']}")
            print(f"     Описание: {conflict['description']}")
            print(f"     Критичность: {conflict['severity']}\n")
            
        # 3. Найти устаревшие ссылки
        print("\n3. Устаревшие ссылки:")
        obsolete = queries.find_obsolete_references()
        for ref in obsolete:
            print(f"   - Документ: {ref['doc_id']}")
            print(f"     Устаревшая ссылка: {ref['obsolete_ref']} → {ref['current_std']}")
            print(f"     {ref['description']}\n")
            
        # 4. Найти документы по термину
        print("\n4. Документы, упоминающие термин 'лонжерон':")
        docs = queries.find_documents_by_term("лонжерон")
        for doc in docs[:5]:
            print(f"   - {doc['doc_id']}: {doc['title']} ({doc['type']})")
            
        # 5. Найти стандарты для спецификации
        print("\n5. Стандарты для спецификации SPEC-WING-001:")
        standards = queries.find_standards_for_specification("SPEC-WING-001")
        for std in standards:
            print(f"   - {std['std_id']}: {std['title']}")
            print(f"     Версия: {std['version']}, Статус: {std['status']}")
            
        # 6. Поиск по содержимому
        print("\n6. Поиск документов со словом 'затяжка':")
        results = queries.search_documents_by_content("затяжка")
        for result in results[:5]:
            print(f"   - {result['doc_id']}: {result['doc_title']}")
            print(f"     Секция: {result['section_id']} - {result['section_title']} (стр. {result['page']})")
            
        # 7. Анализ влияния
        print("\n7. Анализ влияния STD-045 (какие документы зависят от него):")
        impact = queries.get_document_impact_analysis("STD-045")
        for doc in impact:
            print(f"   - {doc['dependent_doc_id']}: {doc['dependent_title']}")
            print(f"     Тип: {doc['dependent_type']}, Статус: {doc['dependent_status']}")
            
        # 8. Определение термина
        print("\n8. Определение термина 'лонжерон':")
        term_info = queries.find_term_definition("лонжерон")
        if term_info:
            print(f"   Термин: {term_info['term']}")
            print(f"   Определение: {term_info['definition']}")
            print(f"   English: {term_info['english']}")
            print(f"   Категория: {term_info['category']}")
            print(f"   Связанные термины: {', '.join(term_info['related_terms'])}")
            
        print("\n" + "=" * 60)
        
    finally:
        queries.close()


if __name__ == "__main__":
    demo_queries()
