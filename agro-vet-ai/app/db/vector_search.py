from typing import Optional

from sqlalchemy import create_engine, text

from app.db.db import build_db_url
from config.config import Config
from app.utils.logger import get_logger

cfg = Config.from_yaml()


class VectorSearchEngine:
    def __init__(self):
        self.db_engine = create_engine(build_db_url())
        self.logger = get_logger(__name__)

    def search_by_embedding(
            self,
            embedding: list[float],
            embedding_column: str,
            content_types: list[str],
            limit: int = cfg.rag.search.doc_limit,
            threshold: float = cfg.rag.search.similarity_threshold,
            source_name: Optional[str] = None,
            source_language: Optional[str] = None,
    ) -> list[dict]:
        """
        Поиск по ближайших эмбеддингов в knowledge_base_chunks

        :param embedding: эмбеддинг поискового запроса.
        :param embedding_column: название колонки с эмбеддингами в БД.
        :param content_types: список с названиями типов чанков среди которых будет произведен поиск.
        :param limit: лимит возвращаемых документов.
        :param threshold: граница по которой отсекаются нерелевантные документы.
        :param source_name: название исходного документа по которому будет произведен поиск.
        :param source_language: язык исходного документа по которому будет произведен поиск.
        """
        try:
            source_name_condition = 'AND sd.name = :source_name' if source_name else ''
            source_language_condition = 'AND sd.language = :source_language' if source_language else ''

            col = f"kbs.{embedding_column}"
            sql_request = text(
                f"""
                    SELECT
                        kbs.content,
                        {col} <=> :embedding AS distance,
                        kbs.chapter_title,
                        kbs.page_number,
                        kbs.chunk_number,
                        sd.name AS source_document,
                        im.image_data
                    FROM knowledge_base_chunks kbs
                    LEFT JOIN source_document sd ON sd.id = kbs.source_document_id
                    LEFT JOIN images im ON im.chunk_id = kbs.id
                    WHERE {col} IS NOT NULL
                        {source_name_condition}
                        {source_language_condition}
                        AND kbs.content_type = ANY(:content_types)
                        AND {col} <=> :embedding <= :threshold
                    ORDER BY {col} <=> :embedding ASC
                    LIMIT :limit
                """
            )

            with self.db_engine.connect() as conn:
                rows = conn.execute(
                    sql_request,
                    parameters={
                        "limit": limit,
                        "embedding": str(embedding),
                        "source_name": source_name,
                        "content_types": content_types,
                        "source_language": source_language,
                        "threshold": threshold
                    }
                ).fetchall()

            data = []
            for row in rows:
                self.logger.info(f'distance: {row.distance} | threshold: {threshold}')
                data.append({
                    'content': row.content,
                    'page_number': row.page_number,
                    'chunk_number': row.chunk_number,
                    'chapter_title': row.chapter_title,
                    'image': row.image_data,
                })

            return data

        except Exception as e:
            self.logger.error(f"❌ [VectorSearch] Ошибка при поиске по эмбеддингам: {e}")
            raise

    def get_figures_chunk(self, figures_names: list[str], source_name: str) -> list[dict]:
        """
        Получение чанков фигур по названиям.

        :param figures_names: список с названиями фигур.
        :param source_name: название исходного документа по которому будет произведен поиск.
        """
        # Если список названий пуст, возвращаем пустой список без выполнения запроса
        if not figures_names:
            return []

        sql_request = text(
            f"""
                SELECT
                    kbs.content,
                    kbs.chapter_title,
                    kbs.page_number,
                    kbs.chunk_number,
                    sd.name AS source_document,
                    im.image_data
                FROM knowledge_base_chunks kbs
                LEFT JOIN source_document sd ON sd.id = kbs.source_document_id
                LEFT JOIN images im ON im.chunk_id = kbs.id
                WHERE kbs.content_type = 'figure' 
                    AND kbs.content_name = ANY(:figures_names)
                    AND sd.name = :source_name
            """
        )

        with self.db_engine.connect() as conn:
            rows = conn.execute(
                sql_request,
                parameters={
                    'source_name': source_name,
                    'figures_names': figures_names
                }
            ).fetchall()

        data = []
        for row in rows:
            data.append({
                'content': row.content,
                'page_number': row.page_number,
                'chunk_number': row.chunk_number,
                'chapter_title': row.chapter_title,
                'image': row.image_data,
            })

        return data

    def get_tables_chunk(self, tables_names: list[str], source_name: str) -> list[dict]:
        """
        Получение чанков таблиц по названиям.

        :param tables_names: список с названиями таблиц.
        :param source_name: название исходного документа по которому будет произведен поиск.
        """
        # Если список названий пуст, возвращаем пустой список без выполнения запроса
        if not tables_names:
            return []

        sql_request = text(
            f"""
                SELECT
                    kbs.content,
                    kbs.chapter_title,
                    kbs.page_number,
                    kbs.chunk_number,
                    sd.name AS source_document
                FROM knowledge_base_chunks kbs
                LEFT JOIN source_document sd ON sd.id = kbs.source_document_id
                WHERE kbs.content_type = 'table' 
                    AND kbs.content_name = ANY(:tables_names)
                    AND sd.name = :source_name
            """
        )

        with self.db_engine.connect() as conn:
            rows = conn.execute(
                sql_request,
                parameters={
                    'source_name': source_name,
                    'tables_names': tables_names
                }
            ).fetchall()

        data = []
        for row in rows:
            data.append({
                'content': row.content,
                'page_number': row.page_number,
                'chunk_number': row.chunk_number,
                'chapter_title': row.chapter_title,
            })

        return data

    def get_bibliography_chunk_by_chunk_number(self, chunk_number: int, source_name: str) -> dict:
        """
        Получение библиографии по номеру чанка.
        Возвращается первый чанк с типом content_type = 'bibliography' у которого номер чанка > chunk_number

        :param chunk_number: номер чанка для которого нужна библиография.
        :param source_name: название исходного документа по которому будет произведен поиск.
        """
        sql_request = text(
            f"""
                SELECT
                    kbs.content,
                    kbs.chapter_title,
                    kbs.page_number,
                    kbs.chunk_number,
                    sd.name AS source_document
                FROM knowledge_base_chunks kbs
                LEFT JOIN source_document sd ON sd.id = kbs.source_document_id
                WHERE kbs.content_type = 'bibliography' 
                    AND sd.name = :source_name
                    AND kbs.chunk_number > :chunk_number
            """
        )

        with self.db_engine.connect() as conn:
            row = conn.execute(
                sql_request,
                parameters={
                    'source_name': source_name,
                    'chunk_number': chunk_number
                }
            ).fetchone()

        return {
            'content': row.content,
            'page_number': row.page_number,
            'chunk_number': row.chunk_number,
            'chapter_title': row.chapter_title,
        }

    def get_chunks_by_page_number(self, page_numbers: list[int], content_types: list[str], source_name: str):
        """
        Получение чанков страницы по номеру страницы.

        :param page_numbers: номера страницы.
        :param content_types: список с названиями типов чанков которые будут возвращены.
        :param source_name: название исходного документа по которому будет произведен поиск.
        """

        sql_request = text(
            f"""
                SELECT
                    kbs.content,
                    kbs.chapter_title,
                    kbs.page_number,
                    kbs.chunk_number,
                    sd.name AS source_document,
                    im.image_data
                FROM knowledge_base_chunks kbs
                LEFT JOIN source_document sd ON sd.id = kbs.source_document_id
                LEFT JOIN images im ON im.chunk_id = kbs.id
                WHERE kbs.page_number = ANY(:page_numbers) 
                    AND kbs.content_type = ANY(:content_types)
                    AND sd.name = :source_name
                ORDER BY kbs.chunk_number ASC
            """
        )

        with self.db_engine.connect() as conn:
            rows = conn.execute(
                sql_request,
                parameters={
                    'page_numbers': page_numbers,
                    'content_types': content_types,
                    'source_name': source_name
                }
            ).fetchall()

        data = []
        for row in rows:
            data.append({
                'content': row.content,
                'page_number': row.page_number,
                'chunk_number': row.chunk_number,
                'chapter_title': row.chapter_title,
                'image': row.image_data,
            })

        return data

    def get_all_book_names(self):
        """
        Получение списка названий книг.
        """
        sql_request = text(
            f"""
                SELECT 
                    name
                FROM source_document
                ORDER BY id
            """
        )

        with self.db_engine.connect() as conn:
            rows = conn.execute(sql_request).fetchall()

        data = [row.name for row in rows]
        return data

    def get_books_meta_info(self, names: list[str]):
        """
        Получение метаинформации по книгам (язык, оглавление).

        :param names: название книги.
        """
        sql_request = text(
            f"""
                SELECT 
                    name,
                    language,
                    contents
                FROM source_document
                WHERE name = ANY(:names)
            """
        )

        with (self.db_engine.connect() as conn):
            rows = conn.execute(
                sql_request,
                parameters={"names": names}
            ).fetchall()

        data = []
        for row in rows:
            data.append({
                'name': row.name,
                'language': row.language,
                'contents': row.contents,
            })

        return data
