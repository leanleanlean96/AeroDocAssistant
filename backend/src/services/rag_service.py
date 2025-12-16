"""RAG (Retrieval-Augmented Generation) сервис"""
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from ..services.document_service import DocumentService
from ..services.embeddings_service import SberEmbeddingsService

logger = logging.getLogger(__name__)


class RAGService:
    """Сервис для работы с RAG архитектурой"""
    
    def __init__(self, doc_service: DocumentService, embeddings_service: SberEmbeddingsService):
        """
        Инициализация RAG сервиса
        
        Args:
            doc_service: Сервис управления документами
            embeddings_service: Сервис embeddings
        """
        self.doc_service = doc_service
        self.embeddings_service = embeddings_service
        self.conversation_history = {}  # ID сессии -> история диалога
    
    async def answer_question(self, question: str, top_k: int = 5, 
                             session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Ответить на вопрос с использованием контекста из документов
        
        Args:
            question: Вопрос
            top_k: Количество контекстных документов
            session_id: ID сессии для истории диалога
            
        Returns:
            Ответ с источниками
        """
        try:
            # Поиск релевантных документов
            relevant_docs = await self.doc_service.search_documents(question, top_k=top_k)
            
            if not relevant_docs:
                return {
                    'question': question,
                    'answer': 'К сожалению, в базе знаний не найдены документы, релевантные вашему запросу.',
                    'sources': [],
                    'confidence': 0.0,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Подготовить контекст
            context = self._prepare_context(relevant_docs)
            
            # Сгенерировать ответ (в реальной системе это был бы вызов LLM)
            answer = await self._generate_answer(question, context, relevant_docs)
            
            # Рассчитать уверенность
            confidence = self._calculate_confidence(relevant_docs)
            
            # Подготовить источники
            sources = self._extract_sources(relevant_docs)
            
            # Сохранить в историю (если указана сессия)
            if session_id:
                if session_id not in self.conversation_history:
                    self.conversation_history[session_id] = []
                
                self.conversation_history[session_id].append({
                    'question': question,
                    'answer': answer,
                    'sources': sources,
                    'timestamp': datetime.now().isoformat()
                })
            
            logger.info(f"Question answered successfully. Confidence: {confidence}")
            
            return {
                'question': question,
                'answer': answer,
                'sources': sources,
                'confidence': confidence,
                'related_documents_count': len(relevant_docs),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            raise
    
    async def _generate_answer(self, question: str, context: str, 
                              relevant_docs: List[Dict[str, Any]]) -> str:
        """
        Генерировать ответ (симуляция LLM)
        
        Args:
            question: Вопрос
            context: Контекст из документов
            relevant_docs: Релевантные документы
            
        Returns:
            Сгенерированный ответ
        """
        try:
            # Это симуляция. В продакшене здесь будет вызов к настоящему LLM
            # например, OpenAI, GigaChat, YandexGPT или локальный Llama
            
            # Простая демонстрация: извлечение ключевых фактов из контекста
            answer_parts = []
            
            answer_parts.append("На основании найденной документации:")
            
            for doc in relevant_docs[:3]:  # Использовать топ-3 документа
                title = doc.get('title', 'Неизвестный документ')
                content_preview = doc.get('content', '')[:200] + '...'
                answer_parts.append(f"\n• {title}: {content_preview}")
            
            answer = "\n".join(answer_parts)
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return "Произошла ошибка при генерации ответа."
    
    def _prepare_context(self, relevant_docs: List[Dict[str, Any]]) -> str:
        """
        Подготовить контекст из документов
        
        Args:
            relevant_docs: Релевантные документы
            
        Returns:
            Текст контекста
        """
        context_parts = []
        
        for doc in relevant_docs:
            context_parts.append(f"---\nДокумент: {doc.get('title', 'Unknown')}")
            context_parts.append(f"Тип: {doc.get('document_type', 'unknown')}")
            context_parts.append(f"Релевантность: {doc.get('similarity', 0):.2%}")
            context_parts.append(f"Содержание:\n{doc.get('content', '')}\n")
        
        return "\n".join(context_parts)
    
    def _extract_sources(self, relevant_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Извлечь информацию об источниках
        
        Args:
            relevant_docs: Релевантные документы
            
        Returns:
            Список источников
        """
        sources = []
        
        for doc in relevant_docs:
            sources.append({
                'id': doc.get('id'),
                'title': doc.get('title', 'Unknown'),
                'document_type': doc.get('document_type', 'other'),
                'doc_number': doc.get('doc_number'),
                'version': doc.get('version', '1.0'),
                'relevance_score': doc.get('similarity', 0),
            })
        
        return sources
    
    def _calculate_confidence(self, relevant_docs: List[Dict[str, Any]]) -> float:
        """
        Рассчитать уверенность ответа
        
        Args:
            relevant_docs: Релевантные документы
            
        Returns:
            Оценка уверенности (0-1)
        """
        if not relevant_docs:
            return 0.0
        
        # Использовать среднюю релевантность
        similarities = [doc.get('similarity', 0) for doc in relevant_docs]
        avg_similarity = sum(similarities) / len(similarities)
        
        # Уверенность зависит от количества и качества документов
        document_confidence = min(len(relevant_docs) / 5, 1.0)  # Max при 5+ документах
        combined_confidence = (avg_similarity + document_confidence) / 2
        
        return min(max(combined_confidence, 0.0), 1.0)
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Получить историю беседы
        
        Args:
            session_id: ID сессии
            
        Returns:
            История диалога
        """
        return self.conversation_history.get(session_id, [])
    
    def clear_conversation_history(self, session_id: str):
        """
        Очистить историю беседы
        
        Args:
            session_id: ID сессии
        """
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            logger.info(f"Conversation history cleared: {session_id}")
    
    async def check_consistency(self, doc_id: str) -> Dict[str, Any]:
        """
        Проверить консистентность документа
        
        Args:
            doc_id: ID документа
            
        Returns:
            Результаты проверки
        """
        try:
            doc = await self.doc_service.get_document(doc_id)
            
            issues = []
            warnings = []
            deprecated_references = []
            contradictions = []
            
            # Проверка 1: Поиск потенциально устаревших ссылок
            deprecated_keywords = ['deprecated', 'устарело', 'outdated', 'old version']
            for keyword in deprecated_keywords:
                if keyword.lower() in doc.content.lower():
                    deprecated_references.append({
                        'keyword': keyword,
                        'message': f'Найдено упоминание про устаревшее: {keyword}'
                    })
            
            # Проверка 2: Поиск противоречивых требований
            if 'должен' in doc.content.lower() and 'не должен' in doc.content.lower():
                contradictions.append({
                    'issue': 'Противоречивые требования',
                    'message': 'В документе найдены противоречивые требования (должен/не должен)'
                })
            
            # Проверка 3: Версионирование
            if doc.version == '1.0':
                warnings.append({
                    'issue': 'Первая версия',
                    'message': 'Документ находится в первой версии, требует дополнительной проверки'
                })
            
            # Проверка 4: Актуальность
            from datetime import datetime, timedelta
            if hasattr(doc, 'created_at'):
                age_days = (datetime.now() - doc.created_at).days
                if age_days > 365:  # Старше года
                    warnings.append({
                        'issue': 'Возраст документа',
                        'message': f'Документ создан {age_days} дней назад, требует актуализации'
                    })
            
            return {
                'document_id': doc_id,
                'document_title': doc.title,
                'issues': issues,
                'warnings': warnings,
                'deprecated_references': deprecated_references,
                'contradictions': contradictions,
                'check_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking consistency: {e}")
            raise
