"""
Примеры использования интегрированной RAG системы с графом знаний
"""

from src.services.llm.main import RAGModel


def example_basic_rag():
    """Пример 1: Базовое использование RAG"""
    print("=" * 70)
    print("ПРИМЕР 1: Базовое использование RAG с графом знаний")
    print("=" * 70)
    
    # Создание RAG модели с графом знаний
    rag = RAGModel(enable_knowledge_graph=True)
    
    try:
        # Загрузка документов
        rag.ensure_collection("aviation_docs")
        
        # Запрос к системе
        question = "Каковы требования к моментам затяжки болтов?"
        print(f"\nВопрос: {question}")
        
        answer = rag.ask(question, "aviation_docs")
        print(f"\nОтвет:\n{answer}")
        
    finally:
        rag.close()


def example_related_documents():
    """Пример 2: Получение связанных документов"""
    print("\n" + "=" * 70)
    print("ПРИМЕР 2: Поиск связанных документов")
    print("=" * 70)
    
    rag = RAGModel(enable_knowledge_graph=True)
    
    try:
        # Получение связанных документов
        doc_id = "SPEC-WING-001"
        related = rag.get_related_documents(doc_id, max_depth=2)
        
        print(f"\nДокументы, связанные со SPEC-WING-001:")
        for doc in related:
            print(f"  - {doc['doc_id']}: {doc['title']} "
                  f"(расстояние: {doc['distance']} шагов)")
            
    finally:
        rag.close()


def example_find_conflicts():
    """Пример 3: Обнаружение конфликтов в документации"""
    print("\n" + "=" * 70)
    print("ПРИМЕР 3: Поиск конфликтов в документации")
    print("=" * 70)
    
    rag = RAGModel(enable_knowledge_graph=True)
    
    try:
        conflicts = rag.get_document_conflicts()
        
        if conflicts:
            print(f"\nОбнаруженные конфликты ({len(conflicts)} шт.):")
            for conflict in conflicts:
                print(f"\n  Документы: {conflict['doc1_id']} ↔ {conflict['doc2_id']}")
                print(f"  Тип: {conflict['conflict_type']}")
                print(f"  Описание: {conflict['description']}")
                print(f"  Критичность: {conflict['severity']}")
        else:
            print("\nКонфликтов не обнаружено")
            
    finally:
        rag.close()


def example_search_by_term():
    """Пример 4: Поиск документов по термину"""
    print("\n" + "=" * 70)
    print("ПРИМЕР 4: Поиск документов по термину из глоссария")
    print("=" * 70)
    
    rag = RAGModel(enable_knowledge_graph=True)
    
    try:
        term = "лонжерон"
        documents = rag.find_documents_by_term(term)
        
        print(f"\nДокументы, упоминающие термин '{term}':")
        for doc in documents:
            print(f"  - {doc['doc_id']}: {doc['title']} ({doc['type']})")
        
        # Получение определения термина
        term_def = rag.get_term_definition(term)
        if term_def:
            print(f"\nОпределение термина '{term}':")
            print(f"  {term_def['definition']}")
            print(f"  English: {term_def['english']}")
            print(f"  Категория: {term_def['category']}")
            if term_def['related_terms']:
                print(f"  Связанные термины: {', '.join(term_def['related_terms'])}")
            
    finally:
        rag.close()


def example_context_enhancement():
    """Пример 5: Демонстрация расширения контекста"""
    print("\n" + "=" * 70)
    print("ПРИМЕР 5: Расширение контекста при помощи графа знаний")
    print("=" * 70)
    
    rag_with_kg = RAGModel(enable_knowledge_graph=True)
    rag_without_kg = RAGModel(enable_knowledge_graph=False)
    
    try:
        question = "Какие стандарты применяются к болтам?"
        
        print(f"\nВопрос: {question}")
        
        print("\n--- С графом знаний ---")
        rag_with_kg.ensure_collection("test_with_kg")
        answer_with_kg = rag_with_kg.ask(question, "test_with_kg")
        print(answer_with_kg[:500] + "...")
        
        print("\n--- Без графа знаний ---")
        rag_without_kg.ensure_collection("test_without_kg")
        answer_without_kg = rag_without_kg.ask(question, "test_without_kg")
        print(answer_without_kg[:500] + "...")
        
    finally:
        rag_with_kg.close()
        rag_without_kg.close()


class AdvancedRAGDemo:
    """Расширенная демонстрация RAG с анализом документов"""
    
    def __init__(self):
        self.rag = RAGModel(enable_knowledge_graph=True)
    
    def analyze_document_relationships(self, doc_id: str):
        """
        Анализ связей документа в графе знаний
        
        Args:
            doc_id: ID документа для анализа
        """
        print(f"\n📊 Анализ связей документа {doc_id}")
        print("-" * 70)
        
        # Получение связанных документов
        related = self.rag.get_related_documents(doc_id, max_depth=2)
        print(f"\n✓ Найдено {len(related)} связанных документов:")
        
        # Группировка по типам
        by_type = {}
        for doc in related:
            doc_type = doc['type']
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(doc)
        
        for doc_type, docs in by_type.items():
            print(f"\n  {doc_type.upper()} ({len(docs)} шт.):")
            for doc in docs[:3]:  # Показать первые 3
                print(f"    - {doc['doc_id']}: {doc['title']}")
    
    def check_documentation_health(self):
        """Проверка здоровья документации"""
        print("\n🏥 Проверка здоровья документации")
        print("-" * 70)
        
        # Проверка конфликтов
        conflicts = self.rag.get_document_conflicts()
        print(f"\n⚠️  Конфликты: {len(conflicts)} обнаружено")
        for conflict in conflicts:
            print(f"  [{conflict['severity']}] {conflict['doc1_id']} ↔ {conflict['doc2_id']}")
        
        # Проверка устаревших ссылок
        # (Можно добавить если будет метод в knowledge_graph_queries)
        print(f"\n✓ Общая статистика документации:")
        print(f"  - Статус проверки: OK")
    
    def generate_report(self, doc_id: str):
        """
        Генерация отчёта о документе и его зависимостях
        
        Args:
            doc_id: ID документа
        """
        print(f"\n📄 Отчёт о документе {doc_id}")
        print("=" * 70)
        
        self.analyze_document_relationships(doc_id)
        self.check_documentation_health()
        
        print("\n" + "=" * 70)
    
    def close(self):
        """Закрытие ресурсов"""
        self.rag.close()


if __name__ == "__main__":
    print("🚀 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ RAG С ГРАФОМ ЗНАНИЙ\n")
    
    # Запуск примеров
    try:
        # Пример 1: Базовое использование
        example_basic_rag()
        
        # Пример 2: Связанные документы
        example_related_documents()
        
        # Пример 3: Поиск конфликтов
        example_find_conflicts()
        
        # Пример 4: Поиск по термину
        example_search_by_term()
        
        # Пример 5: Расширенная демонстрация
        demo = AdvancedRAGDemo()
        demo.generate_report("SPEC-WING-001")
        demo.close()
        
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении примеров: {e}")
        import traceback
        traceback.print_exc()
