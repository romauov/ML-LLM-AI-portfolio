"""Модуль для работы с базой знаний и RAG поиском.

Предоставляет функциональность для подключения к PostgreSQL с pgvector
и выполнения семантического поиска по векторным эмбеддингам.
"""

from typing import List, Optional

import asyncpg

from .config import settings
from .embeddings import get_embeddings_generator

import logging

logger = logging.getLogger(__name__)


# Константы
DEFAULT_LIMIT = 5  # Количество результатов поиска по умолчанию


# Описания источников для инструмента vet_sources
SOURCE_DESCRIPTIONS = {
    "Antimicrobial Therapy in Veterinary Medicine, 5th Edition": (
        "Руководство по антимикробной терапии в ветеринарии, 5-е издание. "
        "Охватывает принципы применения антибиотиков, фармакокинетику, "
        "лечение бактериальных инфекций у различных видов животных."
    ),
    "Practical guide to broiler health management": (
        "Практическое руководство по управлению здоровьем бройлеров. "
        "Охватывает профилактику заболеваний, биобезопасность, "
        "вакцинацию и лечение распространенных болезней птицы."
    ),
    "Болезни свиней": (
        "Справочник по болезням свиней на русском языке. "
        "Описывает симптомы, диагностику и лечение основных "
        "заболеваний свиней в промышленном свиноводстве."
    ),
    "Examination of the pharmacokinetic/pharmacodynamic relationships of orally administered antimicrobials and their correlation with the therapy of various bacterial and mycoplasmal infections in pigs": (
        "Исследование фармакокинетических и фармакодинамических взаимоотношений "
        "антимикробных препаратов при лечении бактериальных и микоплазменных "
        "инфекций у свиней."
    ),
}


class KnowledgeBase:
    """Класс для работы с базой знаний через PostgreSQL и pgvector."""

    def __init__(self):
        """Инициализация базы знаний."""
        self.pool: Optional[asyncpg.Pool] = None
        self.embeddings_generator = get_embeddings_generator()

    async def connect(self):
        """Установка соединения с базой данных."""
        try:
            self.pool = await asyncpg.create_pool(
                host=settings.db_host,
                port=settings.db_port,
                database=settings.db_name,
                user=settings.db_user,
                password=settings.db_password,
                min_size=1,
                max_size=10,
            )
            logger.info(
                f"Подключение к базе данных установлено: "
                f"{settings.db_host}:{settings.db_port}/{settings.db_name}"
            )
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise

    async def close(self):
        """Закрытие соединения с базой данных."""
        if self.pool:
            await self.pool.close()
            logger.info("Соединение с базой данных закрыто")

    async def search(
        self,
        query: str,
        limit: int = None,
        offset: int = 0,
        source_filter: Optional[str] = None,
        include_stats: bool = False,
    ) -> dict:
        """Семантический поиск по базе знаний.

        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов (по умолчанию из настроек)
            offset: Количество результатов для пропуска (пагинация)
            source_filter: Фильтр по источнику документа (опционально)
            include_stats: Включить расширенную статистику в ответ

        Returns:
            Словарь с результатами:
                - results: список найденных чанков (каждый содержит content, source_document,
                           page_number, chapter_title, similarity_score, distance)
                - stats: статистика (если include_stats=True):
                    - total_found: общее количество результатов до применения top_k
                    - returned: количество возвращенных результатов
                    - filtered_out: количество отфильтрованных по порогу
                    - by_source: разбивка по источникам {source: count}
                    - similarity_range: диапазон [min, max] similarity scores

        Raises:
            ValueError: Если запрос пустой или параметры невалидны
            Exception: При ошибках работы с БД или API
        """
        if not query or not query.strip():
            raise ValueError("Поисковый запрос не может быть пустым")

        if limit is None:
            limit = DEFAULT_LIMIT

        if offset < 0:
            raise ValueError("Offset не может быть отрицательным")

        if not self.pool:
            raise RuntimeError("База данных не подключена. Вызовите connect() сначала.")

        try:
            # Генерация эмбеддинга для запроса
            logger.debug(f"Генерация эмбеддинга для запроса: {query[:100]}...")
            query_embedding = await self.embeddings_generator.generate_embedding(query)

            # Конвертация эмбеддинга в формат pgvector
            # Формат: "[0.1234567890, 0.2345678901, ...]" с 10 знаками после запятой
            embedding_str = "[" + ", ".join(f"{x:.10f}" for x in query_embedding) + "]"

            # Формирование SQL запроса
            # Для статистики получаем ВСЕ результаты с distance <= threshold
            # Используем distance напрямую (меньше = лучше), а не 1 - distance
            if source_filter:
                sql = f"""
                    SELECT
                        kbc.content,
                        sd.name AS source_document,
                        kbc.page_number,
                        kbc.chapter_title,
                        kbc.content_type,
                        kbc.content_name,
                        kbc.keywords,
                        kbc.embedding <=> '{embedding_str}' as distance
                    FROM knowledge_base_chunks kbc
                    LEFT JOIN source_document sd ON sd.id = kbc.source_document_id
                    WHERE sd.name = $1
                        AND kbc.embedding IS NOT NULL
                        AND (kbc.embedding <=> '{embedding_str}') <= {settings.similarity_threshold}
                    ORDER BY kbc.embedding <=> '{embedding_str}' ASC
                """
                params = [source_filter]
            else:
                sql = f"""
                    SELECT
                        kbc.content,
                        sd.name AS source_document,
                        kbc.page_number,
                        kbc.chapter_title,
                        kbc.content_type,
                        kbc.content_name,
                        kbc.keywords,
                        kbc.embedding <=> '{embedding_str}' as distance
                    FROM knowledge_base_chunks kbc
                    LEFT JOIN source_document sd ON sd.id = kbc.source_document_id
                    WHERE kbc.embedding IS NOT NULL
                        AND (kbc.embedding <=> '{embedding_str}') <= {settings.similarity_threshold}
                    ORDER BY kbc.embedding <=> '{embedding_str}' ASC
                """
                params = []

            # Выполнение запроса
            logger.debug(f"Выполнение векторного поиска (limit={limit}, offset={offset}, source_filter={source_filter})")
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, *params)

            # Преобразование результатов из БД
            # Фильтрация уже выполнена в SQL запросе (WHERE distance <= threshold)
            all_results = []
            for row in rows:
                distance = float(row["distance"])
                all_results.append({
                    "content": row["content"],
                    "source_document": row["source_document"],
                    "page_number": row["page_number"],
                    "chapter_title": row["chapter_title"],
                    "content_type": row["content_type"],
                    "content_name": row["content_name"],
                    "keywords": row["keywords"] or [],
                    "similarity_score": 1.0 - distance,  # Для обратной совместимости
                    "distance": distance,  # Сохраняем и distance
                })

            # Применяем offset и limit
            results = all_results[offset:offset + limit]

            # Собираем статистику если требуется
            stats = None
            if include_stats and all_results:
                # Группировка по источникам
                by_source = {}
                for res in all_results:
                    source = res["source_document"]
                    by_source[source] = by_source.get(source, 0) + 1

                # Диапазон similarity
                similarities = [res["similarity_score"] for res in all_results]

                stats = {
                    "total_found": len(all_results),
                    "returned": len(results),
                    "by_source": by_source,
                    "similarity_range": {
                        "min": min(similarities),
                        "max": max(similarities)
                    }
                }

            logger.info(
                f"Найдено {len(all_results)} результатов (порог distance <= {settings.similarity_threshold}), "
                f"возвращено {len(results)} (offset={offset}, limit={limit})"
            )

            return {
                "results": results,
                "stats": stats
            }

        except Exception as e:
            logger.error(f"Ошибка при выполнении поиска: {e}")
            raise

    async def get_sources(self) -> List[dict]:
        """Получить список всех источников в базе знаний.

        Returns:
            Список словарей с информацией об источниках:
                - source_document: название источника
                - description: описание источника
                - page_range: диапазон страниц (например, "1-856")
                - chapters_count: количество глав

        Raises:
            Exception: При ошибках работы с БД
        """
        if not self.pool:
            raise RuntimeError("База данных не подключена. Вызовите connect() сначала.")

        try:
            sql = """
                SELECT
                    sd.name AS source_document,
                    MIN(kbc.page_number) as min_page,
                    MAX(kbc.page_number) as max_page,
                    COUNT(DISTINCT kbc.chapter_title) as chapters_count
                FROM knowledge_base_chunks kbc
                LEFT JOIN source_document sd ON sd.id = kbc.source_document_id
                WHERE sd.name IS NOT NULL
                GROUP BY sd.name
                ORDER BY sd.name
            """

            logger.debug("Получение списка источников из БД")
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql)

            results = []
            for row in rows:
                source_name = row["source_document"]
                results.append({
                    "source_document": source_name,
                    "description": SOURCE_DESCRIPTIONS.get(source_name, "Описание недоступно"),
                    "page_range": f"{row['min_page']}-{row['max_page']}",
                    "chapters_count": row["chapters_count"],
                })

            logger.info(f"Найдено {len(results)} источников в базе знаний")
            return results

        except Exception as e:
            logger.error(f"Ошибка при получении списка источников: {e}")
            raise

    async def get_source_info(self, source_document: str) -> dict:
        """Получить детальную информацию об источнике, включая оглавление.

        Args:
            source_document: Название источника

        Returns:
            Словарь с информацией:
                - source_document: название источника
                - page_range: диапазон страниц
                - chapters: список глав с диапазонами страниц

        Raises:
            ValueError: Если источник не найден
            Exception: При ошибках работы с БД
        """
        if not source_document or not source_document.strip():
            raise ValueError("Название источника не может быть пустым")

        if not self.pool:
            raise RuntimeError("База данных не подключена. Вызовите connect() сначала.")

        try:
            # Получение общей информации об источнике
            sql_info = """
                SELECT
                    MIN(kbc.page_number) as min_page,
                    MAX(kbc.page_number) as max_page
                FROM knowledge_base_chunks kbc
                LEFT JOIN source_document sd ON sd.id = kbc.source_document_id
                WHERE sd.name = $1
            """

            # Получение оглавления (список глав)
            sql_chapters = """
                SELECT
                    kbc.chapter_title,
                    MIN(kbc.page_number) as min_page,
                    MAX(kbc.page_number) as max_page
                FROM knowledge_base_chunks kbc
                LEFT JOIN source_document sd ON sd.id = kbc.source_document_id
                WHERE sd.name = $1
                    AND kbc.chapter_title IS NOT NULL
                    AND kbc.chapter_title != ''
                GROUP BY kbc.chapter_title
                ORDER BY MIN(kbc.page_number)
            """

            logger.debug(f"Получение информации об источнике: {source_document}")
            async with self.pool.acquire() as conn:
                info_row = await conn.fetchrow(sql_info, source_document)
                if not info_row or info_row["min_page"] is None:
                    raise ValueError(f"Источник '{source_document}' не найден в базе знаний")

                chapter_rows = await conn.fetch(sql_chapters, source_document)

            # Формирование результата
            chapters = []
            for row in chapter_rows:
                chapters.append({
                    "chapter_title": row["chapter_title"],
                    "page_range": f"{row['min_page']}-{row['max_page']}",
                })

            result = {
                "source_document": source_document,
                "page_range": f"{info_row['min_page']}-{info_row['max_page']}",
                "chapters": chapters,
            }

            logger.info(f"Найдено {len(chapters)} глав для источника '{source_document}'")
            return result

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении информации об источнике: {e}")
            raise

    async def get_pages(
        self,
        source_document: str,
        page_start: int,
        page_end: Optional[int] = None,
    ) -> dict:
        """Получить контент с конкретных страниц источника.

        Args:
            source_document: Название источника
            page_start: Начальная страница
            page_end: Конечная страница (если None, то только page_start)

        Returns:
            Словарь с информацией:
                - source_document: название источника
                - page_range: диапазон страниц
                - pages: список страниц с контентом

        Raises:
            ValueError: Если параметры невалидны
            Exception: При ошибках работы с БД
        """
        if not source_document or not source_document.strip():
            raise ValueError("Название источника не может быть пустым")

        if page_start < 1:
            raise ValueError("Номер страницы должен быть положительным числом")

        if page_end is None:
            page_end = page_start

        if page_end < page_start:
            raise ValueError("Конечная страница не может быть меньше начальной")

        if not self.pool:
            raise RuntimeError("База данных не подключена. Вызовите connect() сначала.")

        try:
            sql = """
                SELECT
                    kbc.page_number,
                    kbc.chapter_title,
                    kbc.content,
                    kbc.chunk_number,
                    kbc.content_type,
                    kbc.content_name
                FROM knowledge_base_chunks kbc
                LEFT JOIN source_document sd ON sd.id = kbc.source_document_id
                WHERE sd.name = $1
                    AND kbc.page_number >= $2
                    AND kbc.page_number <= $3
                ORDER BY kbc.page_number, kbc.chunk_number
            """

            logger.debug(
                f"Получение страниц {page_start}-{page_end} "
                f"из источника '{source_document}'"
            )
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, source_document, page_start, page_end)

            if not rows:
                raise ValueError(
                    f"Страницы {page_start}-{page_end} не найдены "
                    f"в источнике '{source_document}'"
                )

            # Группировка по страницам
            pages_dict = {}
            for row in rows:
                page_num = row["page_number"]
                if page_num not in pages_dict:
                    pages_dict[page_num] = {
                        "page_number": page_num,
                        "chapter_title": row["chapter_title"],
                        "chunks": [],
                    }
                pages_dict[page_num]["chunks"].append({
                    "content": row["content"],
                    "content_type": row["content_type"],
                    "content_name": row["content_name"],
                    "chunk_number": row["chunk_number"],
                })

            # Объединение чанков в единый контент для каждой страницы
            pages = []
            for page_num in sorted(pages_dict.keys()):
                page_data = pages_dict[page_num]
                # Сортируем чанки по chunk_number и объединяем
                sorted_chunks = sorted(page_data["chunks"], key=lambda x: x["chunk_number"])
                content = "\n\n".join(chunk["content"] for chunk in sorted_chunks)

                pages.append({
                    "page_number": page_num,
                    "chapter_title": page_data["chapter_title"],
                    "content": content,
                })

            result = {
                "source_document": source_document,
                "page_range": f"{page_start}-{page_end}",
                "pages": pages,
            }

            logger.info(
                f"Получено {len(pages)} страниц из источника '{source_document}' "
                f"(страницы {page_start}-{page_end})"
            )
            return result

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Ошибка при получении страниц: {e}")
            raise


# Глобальный экземпляр базы знаний
_knowledge_base: Optional[KnowledgeBase] = None


async def get_knowledge_base() -> KnowledgeBase:
    """Получить или создать глобальный экземпляр базы знаний.

    Returns:
        KnowledgeBase: Глобальный экземпляр базы знаний
    """
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
        await _knowledge_base.connect()
    return _knowledge_base
