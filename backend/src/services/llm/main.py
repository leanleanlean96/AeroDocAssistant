import os 
import json
from uuid import uuid4


from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from yandex_gpt import YandexGPT, YandexGPTConfigManagerForAPIKey
from dotenv import load_dotenv
from typing import Any


from .prompts import chunking_prompt, main_prompt


load_dotenv("./env/llm.env")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
CATALOG_ID = os.getenv("CATALOG_ID")


class RAGModel:
    def __init__(self) -> None:
        self.qdrant = QdrantClient(":memory:", prefer_grpc=False)
        self.embedding_model = SentenceTransformer("ai-forever/ru-en-RoSBERTa")
        self.llm_model = YandexGPT(config_manager=YandexGPTConfigManagerForAPIKey(
                                                                                model_type="yandexgpt",
                                                                                catalog_id=CATALOG_ID,
                                                                                api_key=YANDEX_API_KEY
        ))


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
        
        if not context_parts:
            return "Извините, эта информация временно недоступна."
        
        vector_context = "\n".join(context_parts)
        sources_list = " | ".join(sources)

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
        return f"{answer}\n"
    
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
