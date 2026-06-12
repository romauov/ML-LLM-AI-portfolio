"""Модуль генерации эмбеддингов с использованием OpenAI API.

Предоставляет функциональность для генерации векторных представлений текста
с использованием моделей эмбеддингов OpenAI через API VseGPT.
"""

import os
from typing import List

# Удаление переменных окружения прокси для корректной работы OpenAI API
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('ftp_proxy', None)
os.environ.pop('all_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)

from openai import AsyncOpenAI, OpenAIError

from .config import settings

import logging

logger = logging.getLogger(__name__)


class EmbeddingsGenerator:
    """Генератор текстовых эмбеддингов с использованием OpenAI API."""

    def __init__(self):
        """Инициализация генератора эмбеддингов с клиентом OpenAI."""
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
        )
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension


    async def generate_embedding(self, text: str) -> List[float]:
        """Генерация вектора эмбеддинга для одного текста.

        Args:
            text: Входной текст для генерации эмбеддинга

        Returns:
            Список чисел с плавающей точкой, представляющий вектор эмбеддинга

        Raises:
            OpenAIError: Если запрос к API завершился с ошибкой
            ValueError: Если текст пустой или невалидный
        """
        if not text or not text.strip():
            raise ValueError("Текст не может быть пустым")

        try:
            logger.debug(f"Генерация эмбеддинга для текста (длина={len(text)})")
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float",
            )

            embedding = response.data[0].embedding

            # Валидация размерности эмбеддинга
            if len(embedding) != self.dimension:
                logger.warning(
                    f"Неожиданная размерность эмбеддинга: получено {len(embedding)}, "
                    f"ожидалось {self.dimension}"
                )

            logger.debug(f"Эмбеддинг успешно сгенерирован, размерность={len(embedding)}")
            return embedding

        except OpenAIError as e:
            # Улучшенное логирование ошибки с контекстом
            logger.error(f"Ошибка при получении эмбеддинга от API: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при генерации эмбеддинга: {e}")
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Генерация эмбеддингов для нескольких текстов в батче.

        Args:
            texts: Список входных текстов для генерации эмбеддингов

        Returns:
            Список векторов эмбеддингов, по одному для каждого входного текста

        Raises:
            OpenAIError: Если запрос к API завершился с ошибкой
            ValueError: Если любой из текстов пустой или невалидный
        """
        if not texts:
            raise ValueError("Список текстов не может быть пустым")

        # Валидация всех текстов
        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Текст с индексом {i} не может быть пустым")

        try:
            logger.debug(f"Генерация эмбеддингов для батча из {len(texts)} текстов")
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float",
            )

            embeddings = [item.embedding for item in response.data]

            # Валидация всех эмбеддингов
            for i, embedding in enumerate(embeddings):
                if len(embedding) != self.dimension:
                    logger.warning(
                        f"Неожиданная размерность эмбеддинга с индексом {i}: "
                        f"получено {len(embedding)}, ожидалось {self.dimension}"
                    )

            logger.debug(
                f"Успешно сгенерировано {len(embeddings)} эмбеддингов, "
                f"размерность={self.dimension}"
            )
            return embeddings

        except OpenAIError as e:
            # Улучшенное логирование ошибки с контекстом
            logger.error(f"Ошибка при получении эмбеддингов от API: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при генерации батча эмбеддингов: {e}")
            raise

    async def close(self):
        """Закрытие соединения клиента OpenAI."""
        await self.client.close()
        logger.info("Клиент EmbeddingsGenerator закрыт")


# Глобальный экземпляр генератора эмбеддингов
_embeddings_generator: EmbeddingsGenerator | None = None


def get_embeddings_generator() -> EmbeddingsGenerator:
    """Получить или создать глобальный экземпляр генератора эмбеддингов.

    Returns:
        EmbeddingsGenerator: Глобальный экземпляр генератора эмбеддингов
    """
    global _embeddings_generator
    if _embeddings_generator is None:
        _embeddings_generator = EmbeddingsGenerator()
    return _embeddings_generator
