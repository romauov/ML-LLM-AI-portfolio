"""
Исполнитель SQL-запросов для поиска по базе данных препаратов.

Содержит низкоуровневые методы для работы с таблицей drugs_chunks:
- Full-Text Search (search_fts) — поиск кандидатов по терминам через tsvector
- Vector Search (search_vector) — поиск кандидатов по косинусному расстоянию
- Semantic search по кандидатам (search_chunks_by_trade_names) — второй уровень поиска
- Метаданные каталога (get_unique_metadata_values) — уникальные значения для фильтрации
- Секции препарата (get_drug_sections) — по trade_name с фильтром по section_type
- Каталог (get_drugs_by_class, get_available_drug_classes)
- Поиск по названию (find_drugs_by_name) — ILIKE-поиск с ранжированием
- Полная инструкция (get_all_chunks_for_drug) — все чанки препарата для рендеринга файла
"""

from typing import Optional
from sqlalchemy import Engine, text
from app.utils.logger import get_logger


class DrugQueryExecutor:
    """Исполнитель SQL-запросов для поиска препаратов."""

    METADATA_FIELDS = ['trade_name', 'target_animals', 'route', 'dosage_form', 'drug_class', 'manufacturer', 'generic_name']

    def __init__(self, db_engine: Engine):
        self.db_engine = db_engine
        self.logger = get_logger(__name__)

    def get_unique_metadata_values(self) -> dict[str, list[str]]:
        """
        Получение уникальных значений метаданных из базы данных.

        Returns:
            Словарь {field_name: [unique_values]} для полей:
            target_animals, route, dosage_form, drug_class, manufacturer, generic_name
        """
        result = {}
        queries = {
            'trade_name': """
                SELECT DISTINCT trade_name AS val
                FROM drugs_chunks
                WHERE trade_name IS NOT NULL AND trade_name != ''
                ORDER BY val
            """,
            'target_animals': """
                SELECT DISTINCT unnest(target_animals) AS val
                FROM drugs_chunks
                WHERE target_animals IS NOT NULL
                ORDER BY val
            """,
            'route': """
                SELECT DISTINCT route AS val
                FROM drugs_chunks
                WHERE route IS NOT NULL AND route != ''
                ORDER BY val
            """,
            'dosage_form': """
                SELECT DISTINCT dosage_form AS val
                FROM drugs_chunks
                WHERE dosage_form IS NOT NULL AND dosage_form != ''
                ORDER BY val
            """,
            'drug_class': """
                SELECT DISTINCT drug_class AS val
                FROM drugs_chunks
                WHERE drug_class IS NOT NULL AND drug_class != ''
                ORDER BY val
            """,
            'manufacturer': """
                SELECT DISTINCT manufacturer AS val
                FROM drugs_chunks
                WHERE manufacturer IS NOT NULL AND manufacturer != ''
                ORDER BY val
            """,
            'generic_name': """
                SELECT DISTINCT generic_name AS val
                FROM drugs_chunks
                WHERE generic_name IS NOT NULL AND generic_name != ''
                ORDER BY val
            """,
        }

        try:
            with self.db_engine.connect() as conn:
                for field, sql in queries.items():
                    rows = conn.execute(text(sql)).fetchall()
                    result[field] = [row.val for row in rows]
        except Exception as e:
            self.logger.error(f'[QueryExecutor] Ошибка получения метаданных каталога: {e}')
            return {field: [] for field in self.METADATA_FIELDS}

        return result

    def _build_metadata_conditions(
        self,
        metadata_filters: Optional[dict[str, list[str]]]
    ) -> tuple[str, dict]:
        """
        Построение SQL WHERE фрагмента из метаданных.

        Args:
            metadata_filters: Словарь {field_name: [values]} для фильтрации

        Returns:
            Кортеж (sql_fragment, params). sql_fragment пустой если нет фильтров.
        """
        if not metadata_filters:
            return "", {}

        conditions = []
        params = {}

        for field, values in metadata_filters.items():
            if not values:
                continue

            param_name = f"meta_{field}"

            if field == 'target_animals':
                # Array overlap: target_animals && ARRAY[...] (uses GIN index)
                conditions.append(f"target_animals && CAST(:{param_name} AS text[])")
                params[param_name] = values
            else:
                # Case-insensitive fuzzy match: field ILIKE ANY(ARRAY['%val1%', ...])
                ilike_patterns = [f"%{v}%" for v in values]
                conditions.append(f"{field} ILIKE ANY(:{param_name})")
                params[param_name] = ilike_patterns

        if not conditions:
            return "", {}

        sql_fragment = "AND " + " AND ".join(conditions)
        return sql_fragment, params

    def search_by_metadata(
        self,
        metadata_filters: dict[str, list[str]],
        limit: int = 50
    ) -> list[str]:
        """
        Поиск препаратов только по метаданным (без FTS/vector).

        Используется как fallback, когда FTS+vector с фильтрами не дали результатов,
        но метаданные точно описывают запрос (например, "тилозин от Nita-farm").

        Args:
            metadata_filters: Словарь {field_name: [values]} для фильтрации
            limit: Максимальное количество результатов

        Returns:
            Список уникальных trade_name
        """
        metadata_condition, metadata_params = self._build_metadata_conditions(metadata_filters)
        if not metadata_condition:
            return []

        sql = text(f"""
            SELECT DISTINCT trade_name
            FROM drugs_chunks
            WHERE 1=1
                {metadata_condition}
            ORDER BY trade_name
            LIMIT :limit
        """)

        try:
            with self.db_engine.connect() as conn:
                rows = conn.execute(
                    sql,
                    parameters={**metadata_params, "limit": limit}
                ).fetchall()
            return [row.trade_name for row in rows]
        except Exception as e:
            self.logger.error(f'[QueryExecutor] Ошибка поиска по метаданным: {e}')
            return []

    def search_fts(
        self,
        terms: list[str],
        section_types: Optional[list[str]],
        limit: int,
        metadata_filters: Optional[dict[str, list[str]]] = None
    ) -> list[tuple[str, float]]:
        """
        Full-Text Search по чанкам препаратов.

        Args:
            terms: Список поисковых терминов (будут объединены через OR)
            section_types: Фильтр по типам секций (опционально)
            limit: Максимальное количество результатов
            metadata_filters: Фильтры по метаданным (опционально)

        Returns:
            Список кортежей (trade_name, rank)
        """
        # Строим FTS запрос с OR между терминами
        fts_query_parts = []
        fts_params = {}
        for i, term in enumerate(terms):
            param_name = f"fts_term_{i}"
            fts_query_parts.append(f"plainto_tsquery('russian', :{param_name})")
            fts_params[param_name] = term

        fts_query_clause = " || ".join(fts_query_parts)

        section_condition = ""
        if section_types:
            section_condition = "AND section_type = ANY(:section_types)"

        metadata_condition, metadata_params = self._build_metadata_conditions(metadata_filters)

        sql = text(f"""
            SELECT
                trade_name,
                MAX(ts_rank(search_vector, {fts_query_clause})) AS rank
            FROM drugs_chunks
            WHERE search_vector @@ ({fts_query_clause})
                {section_condition}
                {metadata_condition}
            GROUP BY trade_name
            ORDER BY rank DESC
            LIMIT :limit
        """)

        try:
            with self.db_engine.connect() as conn:
                all_params = {
                    **fts_params,
                    **metadata_params,
                    "section_types": section_types,
                    "limit": limit
                }
                rows = conn.execute(sql, parameters=all_params).fetchall()
            return [(row.trade_name, row.rank) for row in rows]
        except Exception as e:
            self.logger.error(f'[QueryExecutor] Ошибка FTS поиска: {e}')
            return []

    def search_vector(
        self,
        embedding: list[float],
        embedding_column: str,
        threshold: float,
        section_types: Optional[list[str]],
        limit: int,
        metadata_filters: Optional[dict[str, list[str]]] = None
    ) -> list[tuple[str, float]]:
        """
        Vector search по чанкам препаратов.

        Args:
            embedding: Вектор запроса
            embedding_column: Название колонки с эмбеддингами в БД
            threshold: Порог косинусного расстояния
            section_types: Фильтр по типам секций (опционально)
            limit: Максимальное количество результатов
            metadata_filters: Фильтры по метаданным (опционально)

        Returns:
            Список кортежей (trade_name, distance)
        """
        section_condition = ""
        if section_types:
            section_condition = "AND section_type = ANY(:section_types)"

        metadata_condition, metadata_params = self._build_metadata_conditions(metadata_filters)

        col = embedding_column
        sql = text(f"""
            SELECT
                trade_name,
                MIN({col} <=> :embedding) AS distance
            FROM drugs_chunks
            WHERE {col} IS NOT NULL
                AND {col} <=> :embedding <= :threshold
                {section_condition}
                {metadata_condition}
            GROUP BY trade_name
            ORDER BY distance ASC
            LIMIT :limit
        """)

        try:
            with self.db_engine.connect() as conn:
                rows = conn.execute(
                    sql,
                    parameters={
                        **metadata_params,
                        "embedding": str(embedding),
                        "threshold": threshold,
                        "section_types": section_types,
                        "limit": limit
                    }
                ).fetchall()
            return [(row.trade_name, row.distance) for row in rows]
        except Exception as e:
            self.logger.error(f'[QueryExecutor] Ошибка векторного поиска: {e}')
            return []

    def search_chunks_by_trade_names(
        self,
        query_embedding: list[float],
        embedding_column: str,
        trade_names: list[str],
        section_types: Optional[list[str]],
        limit: int,
        threshold: float,
    ) -> list[dict]:
        """
        Поиск чанков среди указанных препаратов.

        Args:
            query_embedding: Вектор запроса
            embedding_column: Название колонки с эмбеддингами в БД
            trade_names: Список торговых названий
            section_types: Фильтр по типам секций (опционально)
            limit: Базовый лимит результатов
            threshold: Порог косинусного расстояния

        Returns:
            Список словарей с данными чанков
        """
        section_condition = ""
        vector_filter = ""
        effective_limit = limit

        col = f"dc.{embedding_column}"
        if section_types:
            # Когда указан тип секции, возвращаем все чанки этой секции
            section_condition = "AND dc.section_type = ANY(:section_types)"
            # Увеличиваем лимит чтобы охватить все кандидаты
            effective_limit = limit * len(trade_names)
        else:
            vector_filter = f"AND {col} <=> :embedding <= :threshold"

        sql = text(f"""
            SELECT
                dc.id,
                dc.content,
                dc.section_type,
                dc.section_title,
                dc.trade_name,
                dc.generic_name,
                dc.drug_class,
                dc.dosage_form,
                dc.route,
                dc.manufacturer,
                dc.target_animals,
                dc.source_file,
                dc.source_url,
                {col} <=> :embedding AS distance
            FROM drugs_chunks dc
            WHERE dc.trade_name = ANY(:trade_names)
                AND {col} IS NOT NULL
                {vector_filter}
                {section_condition}
            ORDER BY {col} <=> :embedding ASC
            LIMIT :effective_limit
        """)

        try:
            with self.db_engine.connect() as conn:
                rows = conn.execute(
                    sql,
                    parameters={
                        "embedding": str(query_embedding),
                        "trade_names": trade_names,
                        "section_types": section_types,
                        "threshold": threshold,
                        "effective_limit": effective_limit
                    }
                ).fetchall()

            return [
                {
                    'id': row.id,
                    'content': row.content,
                    'section_type': row.section_type,
                    'section_title': row.section_title,
                    'trade_name': row.trade_name,
                    'generic_name': row.generic_name,
                    'drug_class': row.drug_class,
                    'dosage_form': row.dosage_form,
                    'route': row.route,
                    'manufacturer': row.manufacturer,
                    'target_animals': row.target_animals,
                    'source_file': row.source_file,
                    'source_url': row.source_url,
                    'distance': row.distance
                }
                for row in rows
            ]

        except Exception as e:
            self.logger.error(f'[QueryExecutor] Ошибка поиска чанков: {e}')
            return []

    def get_drug_sections(
        self,
        trade_name: str,
        section_types: Optional[list[str]] = None
    ) -> list[dict]:
        """
        Получение секций препарата по торговому названию.

        Args:
            trade_name: Торговое название препарата
            section_types: Фильтр по типам секций (опционально)

        Returns:
            Список словарей с данными секций
        """
        section_condition = ""
        if section_types:
            section_condition = "AND section_type = ANY(:section_types)"

        sql = text(f"""
            SELECT
                id,
                content,
                section_type,
                section_title,
                trade_name,
                generic_name,
                target_animals
            FROM drugs_chunks
            WHERE trade_name = :trade_name
                {section_condition}
            ORDER BY id ASC
        """)

        try:
            with self.db_engine.connect() as conn:
                rows = conn.execute(
                    sql,
                    parameters={
                        "trade_name": trade_name,
                        "section_types": section_types
                    }
                ).fetchall()

            return [
                {
                    'id': row.id,
                    'content': row.content,
                    'section_type': row.section_type,
                    'section_title': row.section_title,
                    'trade_name': row.trade_name,
                    'generic_name': row.generic_name,
                    'target_animals': row.target_animals
                }
                for row in rows
            ]

        except Exception as e:
            self.logger.error(f'[QueryExecutor] Ошибка получения секций: {e}')
            return []

    def get_drugs_by_class(
        self,
        drug_class: str,
        limit: int = 20
    ) -> list[dict]:
        """
        Получение списка препаратов по классу.

        Args:
            drug_class: Класс препаратов
            limit: Максимальное количество результатов

        Returns:
            Список словарей с метаданными препаратов
        """
        sql = text("""
            SELECT DISTINCT ON (trade_name)
                trade_name,
                generic_name,
                drug_class,
                dosage_form,
                route,
                target_animals,
                manufacturer
            FROM drugs_chunks
            WHERE search_vector @@ plainto_tsquery('russian', :drug_class)
            ORDER BY trade_name ASC
            LIMIT :limit
        """)

        try:
            with self.db_engine.connect() as conn:
                rows = conn.execute(
                    sql,
                    parameters={
                        "drug_class": drug_class,
                        "limit": limit
                    }
                ).fetchall()

            return [
                {
                    'trade_name': row.trade_name,
                    'generic_name': row.generic_name,
                    'drug_class': row.drug_class,
                    'dosage_form': row.dosage_form,
                    'route': row.route,
                    'target_animals': row.target_animals,
                    'manufacturer': row.manufacturer
                }
                for row in rows
            ]

        except Exception as e:
            self.logger.error(f'[QueryExecutor] Ошибка поиска по классу: {e}')
            return []

    def get_available_drug_classes(self) -> list[str]:
        """
        Получение списка доступных классов препаратов.

        Returns:
            Список уникальных классов препаратов
        """
        sql = text("""
            SELECT DISTINCT drug_class
            FROM drugs_chunks
            WHERE drug_class IS NOT NULL
            ORDER BY drug_class
        """)

        try:
            with self.db_engine.connect() as conn:
                rows = conn.execute(sql).fetchall()

            return [row.drug_class for row in rows]

        except Exception as e:
            self.logger.error(f'[QueryExecutor] Ошибка получения классов: {e}')
            return []

    def find_drugs_by_name(self, name_query: str, limit: int = 10) -> list[dict]:
        """
        Поиск препаратов по частичному совпадению названия.

        Args:
            name_query: Часть названия препарата для поиска
            limit: Максимальное количество результатов

        Returns:
            Список словарей с trade_name и generic_name
        """
        sql = text("""
            SELECT DISTINCT ON (trade_name)
                trade_name,
                generic_name
            FROM drugs_chunks
            WHERE trade_name ILIKE '%' || :name_query || '%'
            ORDER BY
                trade_name,
                CASE
                    WHEN trade_name ILIKE :name_query THEN 1
                    WHEN trade_name ILIKE :name_query || '%' THEN 2
                    ELSE 3
                END
            LIMIT :limit
        """)

        try:
            with self.db_engine.connect() as conn:
                rows = conn.execute(
                    sql,
                    parameters={
                        "name_query": name_query,
                        "limit": limit
                    }
                ).fetchall()

            return [
                {
                    'trade_name': row.trade_name,
                    'generic_name': row.generic_name
                }
                for row in rows
            ]

        except Exception as e:
            self.logger.error(f'[QueryExecutor] Ошибка поиска препаратов по названию: {e}')
            return []

    def search_by_generic_name(
        self,
        substance: str,
        animal: str = None,
        section_types: list[str] = None,
        limit: int = 30
    ) -> list[dict]:
        """
        Поиск чанков препаратов по действующему веществу (generic_name) через ILIKE.

        Args:
            substance: Название действующего вещества (или его часть)
            animal: Фильтр по виду животного (опционально)
            section_types: Фильтр по типам секций (опционально)
            limit: Максимальное количество результатов

        Returns:
            Список словарей с данными чанков
        """
        animal_condition = ""
        section_condition = ""

        if animal:
            animal_condition = "AND target_animals && ARRAY[:animal]::text[]"
        if section_types:
            section_condition = "AND section_type = ANY(:section_types)"

        sql = text(f"""
            SELECT
                id,
                content,
                section_type,
                section_title,
                trade_name,
                generic_name,
                drug_class,
                dosage_form,
                route,
                manufacturer,
                target_animals,
                source_file,
                source_url
            FROM drugs_chunks
            WHERE generic_name ILIKE '%' || :substance || '%'
                {animal_condition}
                {section_condition}
            ORDER BY trade_name, id
            LIMIT :limit
        """)

        try:
            with self.db_engine.connect() as conn:
                rows = conn.execute(
                    sql,
                    parameters={
                        "substance": substance,
                        "animal": animal,
                        "section_types": section_types,
                        "limit": limit
                    }
                ).fetchall()

            return [
                {
                    'id': row.id,
                    'content': row.content,
                    'section_type': row.section_type,
                    'section_title': row.section_title,
                    'trade_name': row.trade_name,
                    'generic_name': row.generic_name,
                    'drug_class': row.drug_class,
                    'dosage_form': row.dosage_form,
                    'route': row.route,
                    'manufacturer': row.manufacturer,
                    'target_animals': row.target_animals,
                    'source_file': row.source_file,
                    'source_url': row.source_url,
                }
                for row in rows
            ]

        except Exception as e:
            self.logger.error(f'[QueryExecutor] Ошибка поиска по действующему веществу: {e}')
            return []

    def get_all_chunks_for_drug(self, trade_name: str) -> list[dict]:
        """
        Получение всех чанков препарата для рендеринга инструкции.

        Args:
            trade_name: Точное торговое название препарата

        Returns:
            Список словарей с данными чанков
        """
        sql = text("""
            SELECT
                content,
                section_type,
                section_title,
                generic_name,
                drug_class,
                dosage_form,
                route,
                manufacturer,
                target_animals
            FROM drugs_chunks
            WHERE trade_name = :trade_name
            ORDER BY id ASC
        """)

        try:
            with self.db_engine.connect() as conn:
                rows = conn.execute(
                    sql,
                    parameters={"trade_name": trade_name}
                ).fetchall()

            return [
                {
                    'content': row.content,
                    'section_type': row.section_type,
                    'section_title': row.section_title,
                    'generic_name': row.generic_name,
                    'drug_class': row.drug_class,
                    'dosage_form': row.dosage_form,
                    'route': row.route,
                    'manufacturer': row.manufacturer,
                    'target_animals': row.target_animals
                }
                for row in rows
            ]

        except Exception as e:
            self.logger.error(f'[QueryExecutor] Ошибка получения чанков препарата: {e}')
            return []
