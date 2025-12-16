"""Сервис работы с Sber Embeddings"""
import httpx
import logging
from typing import List
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np

logger = logging.getLogger(__name__)


class SberEmbeddingsService:
    """Сервис для работы с Sber Embeddings API"""
    
    def __init__(self, api_key: str, api_url: str):
        """
        Инициализация сервиса
        
        Args:
            api_key: API ключ Sber
            api_url: URL API Sber
        """
        self.api_key = api_key
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self._executor = ThreadPoolExecutor(max_workers=5)
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Получить embedding для текста через Sber API
        
        Args:
            text: Текст для embeddings
            
        Returns:
            Вектор embedding
        """
        if not text or len(text.strip()) == 0:
            # Возвращать нулевой вектор для пустого текста
            return [0.0] * 1024
        
        try:
            # Для демонстрации: генерируем детерминированный embedding
            # В продакшене это будет настоящий вызов к Sber API
            embedding = await self._generate_mock_embedding(text)
            logger.info(f"Embedding generated for text length: {len(text)}")
            return embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            # Возвращать нулевой вектор при ошибке
            return [0.0] * 1024
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Получить embeddings для списка текстов
        
        Args:
            texts: Список текстов
            
        Returns:
            Список векторов embeddings
        """
        embeddings = []
        for text in texts:
            embedding = await self.get_embedding(text)
            embeddings.append(embedding)
        
        logger.info(f"Batch embeddings generated for {len(texts)} texts")
        return embeddings
    
    async def _generate_mock_embedding(self, text: str) -> List[float]:
        """
        Генерировать mock embedding (для демонстрации)
        В продакшене это будет вызов к реальному API
        
        Args:
            text: Текст для embedding
            
        Returns:
            Вектор embedding размером 1024
        """
        # Детерминированное создание embedding на основе текста
        seed = hash(text) % (2**32)
        np.random.seed(seed)
        embedding = np.random.randn(1024).astype(np.float32)
        
        # Нормализация
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        return embedding.tolist()
    
    async def _call_sber_api(self, text: str) -> List[float]:
        """
        Вызов реального Sber Embeddings API
        
        Args:
            text: Текст для embedding
            
        Returns:
            Вектор embedding
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "input": text,
            "model": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        }
        
        try:
            response = await self.client.post(
                f"{self.api_url}/embeddings",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                return data['data'][0]['embedding']
            else:
                logger.error(f"Unexpected Sber API response: {data}")
                return [0.0] * 1024
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Sber API HTTP error: {e}")
            return [0.0] * 1024
        except Exception as e:
            logger.error(f"Error calling Sber API: {e}")
            return [0.0] * 1024
    
    async def close(self):
        """Закрыть HTTP клиент"""
        await self.client.aclose()
        self._executor.shutdown(wait=True)
    
    def __del__(self):
        """Очистка ресурсов"""
        try:
            asyncio.run(self.close())
        except:
            pass
