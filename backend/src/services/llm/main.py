import os 
import json
from uuid import uuid4
from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, ScoredPoint
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from yandex_gpt import YandexGPT, YandexGPTConfigManagerForAPIKey

from ...config import (
    YANDEX_API_KEY, CATALOG_ID, QDRANT_COLLECTION_NAME,
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP,
    MAX_CONTEXT_TOKENS, SIMILARITY_THRESHOLD
)
from .prompts import chunking_prompt, main_prompt


class RAGModel:
    def __init__(self, collection_name: str = QDRANT_COLLECTION_NAME) -> None:
        self.collection_name = collection_name
        self.qdrant = QdrantClient(":memory:", prefer_grpc=False)
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.llm_model = YandexGPT(config_manager=YandexGPTConfigManagerForAPIKey(
            model_type="yandexgpt",
            catalog_id=CATALOG_ID,
            api_key=YANDEX_API_KEY
        ))
        self.ensure_collection(collection_name)


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
    def make_chunks(long_text: str) -> List[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", "! ", "? "]
        )
        chunks: List[str] = splitter.split_text(long_text)
        return chunks


    def clear_text_to_embedding(self, text: str) -> str:
        message: list[dict[str, Any]] = [{"role": "user", "text": f"""{chunking_prompt} 
                                           обработай следующий текст: 
                                           {text}"""}]
        
        result: str = self.llm_model.get_sync_completion(messages=message, temperature=0.1)
        
        return result


    def read_json_and_add_point(self, doc_path: str) -> None:
        """Чтение JSON и добавление точек (для обратной совместимости)"""
        with open(doc_path, 'r', encoding='utf-8') as file:
            data = json.loads(file.read())
            for doc in data.get('documents', []):
                if doc.get('text_entities'):
                    full_text: List[str] = []
                    for text in doc.get('text_entities', []):
                        if text.get('type') == 'plain':
                            clear_text = text.get('text', '').replace('\n', ' ').strip().lower()
                            if clear_text:
                                full_text.append(clear_text)

                    if full_text:
                        text_to_embedd = ' '.join(full_text)
                        try:
                            text_to_embedd = self.clear_text_to_embedding(text_to_embedd)
                        except:
                            pass  # Используем оригинальный текст при ошибке
                        text_chunks = self.make_chunks(text_to_embedd)
                    
                        for chunk in text_chunks:
                            if chunk.strip():
                                payload = {
                                    "content": chunk,
                                    "metadata": { 
                                        "doc_id": doc.get('doc_name', 'unknown'),
                                        "doc_name": doc.get('doc_name', 'unknown'),
                                        "doc_chapter": doc.get('doc_chapter', '')
                                    }
                                }
                                self.add_point(self.collection_name, chunk, payload)


    def search(self, query: str, limit: int = 10, min_score: float = SIMILARITY_THRESHOLD, 
               filter_docs: Optional[List[str]] = None) -> List[Tuple[ScoredPoint, Dict[str, Any]]]:
        """Семантический поиск с фильтрацией"""
        query_vector = self.get_embeddings(query)
        
        # Фильтр по документам, если указан
        query_filter = None
        if filter_docs:
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchAny
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="metadata.doc_id",
                            match=MatchAny(any=filter_docs)
                        )
                    ]
                )
            except ImportError:
                # Fallback если MatchAny недоступен
                pass
        
        search_results = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            score_threshold=min_score,
            query_filter=query_filter,
            with_payload=True
        )
        
        results = []
        for point in search_results.points:
            if point.score >= min_score:
                results.append((point, {
                    "content": point.payload.get("content", ""),
                    "metadata": point.payload.get("metadata", {}),
                    "score": point.score
                }))
        
        return results
    
    def rag_query(self, user_question: str, max_context_tokens: int = MAX_CONTEXT_TOKENS,
                  filter_docs: Optional[List[str]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """RAG запрос с возвратом цитат"""
        search_results = self.search(user_question, limit=10, filter_docs=filter_docs)
        
        context_parts: List[str] = []
        citations: List[Dict[str, Any]] = []
        total_tokens: int = 0
        
        for point, data in search_results:
            content: str = data["content"]
            metadata: Dict[str, Any] = data["metadata"]
            
            doc_name = metadata.get("doc_name", metadata.get("doc_id", "Неизвестно"))
            doc_chapter = metadata.get("doc_chapter", metadata.get("chapter", "Не указано"))
            chunk_id = str(point.id)
            
            context_parts.append(f"[Чанк {len(context_parts)+1}] {content}")
            citations.append({
                "document_name": doc_name,
                "chapter": doc_chapter,
                "chunk_id": chunk_id,
                "text": content[:200] + "..." if len(content) > 200 else content
            })
            
            total_tokens += len(content.split())
            if total_tokens > max_context_tokens:
                break
        
        if not context_parts:
            return "Извините, эта информация временно недоступна.", []
        
        vector_context = "\n".join(context_parts)
        sources_list = " | ".join([f"{c['document_name']} ({c['chapter']})" for c in citations])

        messages = [
            {
                "role": "system", 
                "text": f"""{main_prompt} 
<НАЧАЛО ВЕКТОРНОГО КОНТЕКСТА>
{vector_context}
<КОНЕЦ ВЕКТОРНОГО КОНТЕКСТА>

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
        return answer, citations
    
    def ensure_collection(self, collection_name: str) -> None:
        try:
            collections = self.qdrant.get_collections()
            if collection_name not in [c.name for c in collections.collections]:
                self.create_collection(collection_name)
        except Exception as e:
            print(f"An error occured: {e}")


    def add_document_chunks(self, text: str, doc_id: str, doc_name: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> int:
        """Добавить чанки документа в коллекцию"""
        if not text.strip():
            return 0
        
        # Очистка текста через LLM (опционально, можно пропустить для ускорения)
        try:
            processed_text = self.clear_text_to_embedding(text)
        except:
            processed_text = text
        
        chunks = self.make_chunks(processed_text)
        chunk_count = 0
        
        for chunk in chunks:
            if chunk.strip():
                payload = {
                    "content": chunk,
                    "metadata": {
                        "doc_id": doc_id,
                        "doc_name": doc_name,
                        **(metadata or {})
                    }
                }
                self.add_point(self.collection_name, chunk, payload)
                chunk_count += 1
        
        return chunk_count
    
    def load_documents(self, docs_path: str) -> int:
        """Загрузка документов из директории (для обратной совместимости)"""
        total_chunks = 0
        try:
            if os.path.isdir(docs_path):
                for doc in os.listdir(docs_path):
                    if doc.endswith(".json"):
                        self.read_json_and_add_point(os.path.join(docs_path, doc))
            else:
                if docs_path.endswith(".json"):
                    self.read_json_and_add_point(docs_path)
        except Exception as e:
            print(f"An error occured: {e}")
        return total_chunks

    def ask(self, user_question: str, filter_docs: Optional[List[str]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """Вопрос-ответ с возвратом цитат"""
        return self.rag_query(user_question, filter_docs=filter_docs)
    
    def close(self) -> None:
        self.qdrant.close()
