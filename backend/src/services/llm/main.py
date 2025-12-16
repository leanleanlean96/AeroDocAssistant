import os 
import json
from uuid import uuid4
from typing import Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

from .prompts import chunking_prompt, main_prompt
from .knowledge_graph_queries import KnowledgeGraphQueries

# Попытка импорта Yandex GPT (опционально)
try:
    from yandex_gpt import YandexGPT, YandexGPTConfigManager
except ImportError:
    try:
        from yandexgpt_python import YandexGPT, YandexGPTConfigManager
    except ImportError:
        YandexGPT = None
        YandexGPTConfigManager = None
        print("⚠️  YandexGPT недоступен. LLM функции будут ограничены.")


load_dotenv("./env/llm.env")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
CATALOG_ID = os.getenv("CATALOG_ID")


class RAGModel:
    def __init__(self, enable_knowledge_graph: bool = True) -> None:
        self.qdrant = QdrantClient(":memory:", prefer_grpc=False)
        self.embedding_model = SentenceTransformer("ai-forever/ru-en-RoSBERTa")
        
        # Инициализация LLM модели (опционально)
        self.llm_model = None
        if YandexGPT:
            try:
                self.llm_model = YandexGPT(
                    api_key=os.getenv("YANDEX_API_KEY", "dummy_key"),
                    catalog_id=os.getenv("CATALOG_ID", "dummy_catalog")
                )
            except Exception as e:
                print(f"⚠️  Не удалось инициализировать YandexGPT: {e}")
        
        # Интеграция с графом знаний
        self.knowledge_graph = None
        self.enable_kg = enable_knowledge_graph
        if enable_knowledge_graph:
            try:
                self.knowledge_graph = KnowledgeGraphQueries()
                print("✓ Граф знаний успешно подключен")
            except Exception as e:
                print(f"⚠ Граф знаний недоступен: {e}")
                self.enable_kg = False


    def get_embeddings(self, text:str, task:str="поиск по документам") -> list[float]:
        prefixed_text: str = f"{task}: {text}"
        embedding: list[float] = self.embedding_model.encode(
            prefixed_text,
            normalize_embeddings=True,
            convert_to_numpy=False,
            show_progress_bar=False
        ).tolist()
        return embedding


    def create_collection(self, collection_name: str) -> None:
        size = len(self.get_embeddings("test"))
        self.qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=size, distance=Distance.COSINE)
        )


    def add_point(self, collection_name: str, text: str, payload: dict[str, Any]) -> None:
        self.qdrant.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=str(uuid4().hex),
                    vector=self.get_embeddings(text),
                    payload=payload
                )
            ])


    @staticmethod
    def make_chunks(long_text: str) -> list[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50,
            separators=["\n\n","\n", ". ", "! ", "? ", ]
        )
        chunks: list[str] = splitter.split_text(long_text)
        print(chunks)
        return chunks


    def clear_text_to_embedding(self, text: str) -> str:
        message: list[dict[str, Any]] = [{"role": "user", "text": f"""{chunking_prompt} 
                                           обработай следующий текст: 
                                           {text}"""}]
        
        result: str = self.llm_model.get_sync_completion(messages=message, temperature=0.1)
        
        return result


    def read_json_and_add_point(self, doc_path: str, collection_name: str) -> None:
        with open(doc_path, 'r') as file:
            data = json.loads(file.read())
            for doc in data.get('documents'):
                if doc.get('text_entities'):
                    full_text: list[str] = []
                    for text in doc.get('text_entities'):
                        if text.get('type') == 'plain':
                            clear_text = text.get('text').replace('\n', ' ').strip().lower()
                            full_text.append(clear_text)


                    text_to_embedd = ' '.join(full_text)
                    text_to_embedd = self.clear_text_to_embedding(text_to_embedd)
                    text_chunks = self.make_chunks(text_to_embedd)
                
                    for chunk in text_chunks:
                        payload = {
                            "content": chunk,
                            "metadata": { 
                                "doc_name": doc.get('doc_name'),
                                "doc_chapter": doc.get('doc_chapter')
                            }
                        }
                        self.add_point(collection_name, chunk, payload)


    def rag_query(self, collection_name: str, user_question: str, max_context_tokens: int=1000) -> str:
        """
        Выполнить RAG запрос с опциональной интеграцией графа знаний
        
        Args:
            collection_name: Название коллекции Qdrant
            user_question: Вопрос пользователя
            max_context_tokens: Максимальное количество токенов в контексте
            
        Returns:
            Ответ LLM с указанием источников
        """
        # Поиск в Qdrant
        search_results = self.qdrant.query_points(
            collection_name=collection_name,
            query=self.get_embeddings(user_question),
            limit=10,
            with_payload=True
        )
        
        context_parts: list[str] = []
        sources: list[str] = []
        total_tokens: int = 0
        
        for point in search_results.points:
            if point.score >= 0.65:
                content: str = point.payload.get('content', '')
                metadata: Any = point.payload.get('metadata', {})
                source_info = f"{metadata.get('doc_name', 'Неизвестно')} ({metadata.get('doc_chapter', 'Не указано')})"
                
                context_parts.append(f"[Чанк {len(context_parts)+1}] {content}")
                sources.append(source_info)
                
                total_tokens += len(content.split())
                if total_tokens > max_context_tokens:
                    break
        
        # Расширение контекста с помощью графа знаний
        related_docs_context = ""
        if self.enable_kg and self.knowledge_graph:
            related_docs_context = self._enhance_context_with_knowledge_graph(
                user_question, 
                sources
            )
        
        if not context_parts and not related_docs_context:
            return "Извините, эта информация временно недоступна."
        
        vector_context = "\n".join(context_parts)
        sources_list = " | ".join(sources)

        # Подготовка промпта с контекстом графа знаний
        kg_context_prompt = ""
        if related_docs_context:
            kg_context_prompt = f"""
<НАЧАЛО КОНТЕКСТА ИЗ ГРАФА ЗНАНИЙ>
{related_docs_context}
<КОНЕЦ КОНТЕКСТА ИЗ ГРАФА ЗНАНИЙ>

ИСПОЛЬЗУЙ ИНФОРМАЦИЮ ИЗ ГРАФА ЗНАНИЙ для дополнения ответа связанными документами и требованиями.
"""

        messages = [
            {
                "role": "system", 
                "text": f"""{main_prompt} 
<НАЧАЛО ВЕКТОРНОГО КОНТЕКСТА>
{vector_context}
<КОНЕЦ ВЕКТОРНОГО КОНТЕКСТА>
{kg_context_prompt}

ВАЖНО: В конце ответа обязательно укажи источники информации в формате:
Источники: [список документов через запятую]

Пример: Источники: Трудовой кодекс РФ (Охрана труда), Правила пожарной безопасности (Общие положения)"""
            },
            {
                "role": "user", 
                "text": f"{user_question}\n\nИсточники для ответа: {sources_list}"
            }
        ]
        
        answer: str = self.llm_model.get_sync_completion(messages=messages, temperature=0.1)
        return f"{answer}\n"
    
    def _enhance_context_with_knowledge_graph(self, user_question: str, current_sources: list[str]) -> str:
        """
        Расширить контекст документов с помощью графа знаний
        
        Args:
            user_question: Вопрос пользователя
            current_sources: Текущие источники из Qdrant
            
        Returns:
            Дополнительный контекст из графа знаний
        """
        try:
            enhanced_context = []
            
            # 1. Поиск по содержимому
            content_results = self.knowledge_graph.search_documents_by_content(user_question)
            if content_results:
                enhanced_context.append("📄 Связанные документы в системе:")
                for doc in content_results[:5]:  # Топ 5
                    enhanced_context.append(f"  - {doc['doc_id']}: {doc['doc_title']} "
                                          f"(секция: {doc['section_title']})")
            
            # 2. Поиск конфликтов, если они релевантны
            conflicts = self.knowledge_graph.find_conflicts()
            if conflicts:
                enhanced_context.append("\n⚠️ Обнаруженные конфликты в документации:")
                for conflict in conflicts[:3]:  # Топ 3
                    if 'затяжка' in user_question.lower() or 'болт' in user_question.lower():
                        enhanced_context.append(f"  - {conflict['doc1_id']} ↔ {conflict['doc2_id']}: "
                                              f"{conflict['description']}")
            
            # 3. Поиск устаревших ссылок
            obsolete = self.knowledge_graph.find_obsolete_references()
            if obsolete:
                enhanced_context.append("\n🔄 Устаревшие ссылки:")
                for ref in obsolete[:3]:  # Топ 3
                    enhanced_context.append(f"  - {ref['obsolete_ref']} → {ref['current_std']}")
            
            return "\n".join(enhanced_context)
            
        except Exception as e:
            print(f"Ошибка при расширении контекста из графа знаний: {e}")
            return ""
    
    def get_related_documents(self, doc_id: str, max_depth: int = 2) -> list[dict]:
        """
        Получить связанные документы из графа знаний
        
        Args:
            doc_id: ID документа
            max_depth: Максимальная глубина связей
            
        Returns:
            Список связанных документов
        """
        if not self.enable_kg or not self.knowledge_graph:
            return []
        
        try:
            return self.knowledge_graph.find_related_documents(doc_id, max_depth)
        except Exception as e:
            print(f"Ошибка при получении связанных документов: {e}")
            return []
    
    def get_document_conflicts(self) -> list[dict]:
        """Получить все конфликты в документации"""
        if not self.enable_kg or not self.knowledge_graph:
            return []
        
        try:
            return self.knowledge_graph.find_conflicts()
        except Exception as e:
            print(f"Ошибка при получении конфликтов: {e}")
            return []
    
    def find_documents_by_term(self, term: str) -> list[dict]:
        """Найти документы, упоминающие определённый термин"""
        if not self.enable_kg or not self.knowledge_graph:
            return []
        
        try:
            return self.knowledge_graph.find_documents_by_term(term)
        except Exception as e:
            print(f"Ошибка при поиске по термину: {e}")
            return []
    
    def get_term_definition(self, term: str) -> Optional[dict]:
        """Получить определение термина из глоссария"""
        if not self.enable_kg or not self.knowledge_graph:
            return None
        
        try:
            return self.knowledge_graph.find_term_definition(term)
        except Exception as e:
            print(f"Ошибка при получении определения: {e}")
            return None
    
    def ensure_collection(self, collection_name: str) -> None:
        try:
            collections = self.qdrant.get_collections()
            if collection_name not in [c.name for c in collections.collections]:
                self.create_collection(collection_name)
        except Exception as e:
            print(f"An error occured: {e}")


    def load_documents(self, docs_path: str, collection_name: str) -> None:
        self.ensure_collection(collection_name)
        try:
            if os.path.isdir(docs_path):
                for doc in os.listdir(docs_path):
                    if doc.endswith(".json"):
                        self.read_json_and_add_point(os.path.join(docs_path, doc), collection_name)
            else:
                if docs_path.endswith(".json"):
                    self.read_json_and_add_point(docs_path, collection_name)
        except Exception as e:
            print(f"An error occured: {e}")


    def ask(self, user_question: str, collection_name: str) -> str:
        return self.rag_query(collection_name, user_question)
    
    def close(self) -> None:
        self.qdrant.close()
        if self.knowledge_graph:
            self.knowledge_graph.close()
