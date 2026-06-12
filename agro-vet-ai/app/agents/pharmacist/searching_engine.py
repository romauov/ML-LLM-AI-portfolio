"""
Движок поиска по базе данных препаратов.

Реализует двухуровневый гибридный поиск с параллельными каналами retrieval:
1. Поиск кандидатов: Metadata + FTS + Vector как три параллельных канала, merge через RRF
2. Семантический поиск (Semantic): vector search по чанкам кандидатов
"""

from typing import Optional
from sqlalchemy import create_engine
from app.db.db import build_db_url
from app.llm.providers.llm_provider import LLMProvider
from app.utils.logger import get_logger
from .query_processing import DiseaseQueryExpander
from .search.query_executor import DrugQueryExecutor
from .search.fusion import RRFFusion
from .search.formatters import MarkdownFormatter
from config.config import Config

cfg = Config.from_yaml()


class DrugSearchEngine:
    """Движок поиска по базе данных препаратов."""

    _instance: Optional["DrugSearchEngine"] = None

    def __new__(cls) -> "DrugSearchEngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.db_engine = create_engine(build_db_url())
        self.llm_provider = LLMProvider()
        self.logger = get_logger(__name__)
        self.query_expander = DiseaseQueryExpander()
        self.query_executor = DrugQueryExecutor(self.db_engine)
        self.rrf_fusion = RRFFusion(k=60)
        self.formatter = MarkdownFormatter()
        self._metadata_cache: Optional[dict[str, list[str]]] = None

    def search_drugs(
        self,
        query: str,
        section_types: Optional[list[str]] = None,
        limit: int = 30,
        coarse_limit: int = 50,
        threshold: float = 0.6,
        metadata_filters: Optional[dict[str, list[str]]] = None,
    ) -> list[dict]:
        """
        Двухуровневый поиск по препаратам с параллельными каналами retrieval.

        Три канала поиска кандидатов (объединяются через RRF):
        - Metadata: точное совпадение по SQL-фильтрам (trade_name, manufacturer, etc.)
        - FTS: полнотекстовый поиск с морфологией
        - Vector: семантический поиск по эмбеддингам

        Args:
            query: Поисковый запрос
            section_types: Фильтр по типам секций (опционально)
            limit: Максимальное количество возвращаемых чанков
            coarse_limit: Максимальное количество кандидатов на первом уровне
            threshold: Порог косинусного расстояния
            metadata_filters: Фильтры по метаданным (опционально)

        Returns:
            Список словарей с данными чанков
        """
        self.logger.info(f'[DrugSearch] Поиск по запросу: "{query}"')
        if metadata_filters:
            self.logger.info(f'[DrugSearch] Метаданные фильтры: {metadata_filters}')

        # Step 1: Metadata retrieval — всегда когда есть фильтры
        metadata_candidates = []
        if metadata_filters:
            names = self.query_executor.search_by_metadata(
                metadata_filters=metadata_filters,
                limit=coarse_limit
            )
            metadata_candidates = [(name, 1.0) for name in names]
            self.logger.info(f'[DrugSearch] Metadata канал: {len(metadata_candidates)} кандидатов')

        # Step 2: FTS + Vector поиск кандидатов, merge через RRF
        embedding_result = self.llm_provider.vectorize(query)
        query_embedding = embedding_result.vector
        embedding_column = embedding_result.column

        expanded_terms = self.query_expander.expand_query(query)
        fts_rows = self.query_executor.search_fts(
            terms=expanded_terms,
            section_types=section_types,
            limit=coarse_limit
        )
        vector_rows = self.query_executor.search_vector(
            embedding=query_embedding,
            embedding_column=embedding_column,
            threshold=threshold + 0.2,
            section_types=section_types,
            limit=coarse_limit
        )

        self.logger.info(
            f'[DrugSearch] FTS канал: {len(fts_rows)} кандидатов '
            f'(расширено до {len(expanded_terms)} терминов: {expanded_terms})'
        )
        self.logger.info(f'[DrugSearch] Vector канал: {len(vector_rows)} кандидатов')

        sources = []
        if metadata_candidates:
            sources.append((metadata_candidates, 20.0))
        if fts_rows:
            sources.append((fts_rows, 10.0))
        if vector_rows:
            sources.append((vector_rows, 1.0))

        fused = self.rrf_fusion.merge_multiple(sources) if sources else []
        candidate_trade_names = [name for name, _ in fused[:coarse_limit]]

        if not candidate_trade_names:
            self.logger.warning('[DrugSearch] Кандидаты не найдены')
            return []

        self.logger.info(f'[DrugSearch] Найдено {len(candidate_trade_names)} кандидатов')

        # Step 3: Chunk retrieval
        chunks = self.query_executor.search_chunks_by_trade_names(
            query_embedding=query_embedding,
            embedding_column=embedding_column,
            trade_names=candidate_trade_names,
            section_types=section_types,
            limit=limit,
            threshold=threshold,
        )

        self.logger.info(f'[DrugSearch] Возвращено {len(chunks)} чанков')
        return chunks

    # =====================================================================
    # Публичные методы - делегируют в query_executor (обратная совместимость)
    # =====================================================================

    def get_unique_metadata_values(self) -> dict[str, list[str]]:
        """Делегирует в query_executor с кешированием результата."""
        if self._metadata_cache is None:
            self._metadata_cache = self.query_executor.get_unique_metadata_values()
        return self._metadata_cache

    def get_drug_sections(
        self,
        trade_name: str,
        section_types: Optional[list[str]] = None
    ) -> list[dict]:
        """Делегирует в query_executor.get_drug_sections()."""
        return self.query_executor.get_drug_sections(trade_name, section_types)

    def get_drugs_by_class(self, drug_class: str, limit: int = 20) -> list[dict]:
        """Делегирует в query_executor.get_drugs_by_class()."""
        return self.query_executor.get_drugs_by_class(drug_class, limit)

    def get_available_drug_classes(self) -> list[str]:
        """Делегирует в query_executor.get_available_drug_classes()."""
        return self.query_executor.get_available_drug_classes()

    def find_drugs_by_name(self, name_query: str, limit: int = 10) -> list[dict]:
        """Делегирует в query_executor.find_drugs_by_name()."""
        return self.query_executor.find_drugs_by_name(name_query, limit)

    def search_by_generic_name(
        self,
        generic_name: str,
        animal: str = None,
        section_types: list[str] = None,
        limit: int = 30
    ) -> list[dict]:
        """Делегирует в query_executor.search_by_generic_name()."""
        return self.query_executor.search_by_generic_name(generic_name, animal, section_types, limit)

    def get_drug_instruction_as_markdown(self, trade_name: str) -> Optional[str]:
        """
        Получение полной инструкции препарата в формате Markdown.

        Делегирует в query_executor для получения чанков и formatter для рендеринга.
        """
        chunks = self.query_executor.get_all_chunks_for_drug(trade_name)
        if not chunks:
            return None
        return self.formatter.format_drug_instruction(trade_name, chunks)
