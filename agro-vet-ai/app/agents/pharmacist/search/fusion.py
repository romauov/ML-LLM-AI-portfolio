"""
Алгоритмы ранжирования и слияния результатов поиска.

Содержит:
- Reciprocal Rank Fusion (RRF)
- Потенциально другие алгоритмы в будущем
"""


class RRFFusion:
    """
    Reciprocal Rank Fusion для объединения результатов из разных источников.

    RRF формула: score = sum(1 / (k + rank_i))
    где k - константа сглаживания (обычно 60)
    """

    def __init__(self, k: int = 60):
        """
        Args:
            k: Константа сглаживания для RRF (по умолчанию 60)
        """
        self.k = k

    def merge(
        self,
        fts_results: list[tuple[str, float]],
        vector_results: list[tuple[str, float]],
        fts_weight: float = 10.0,
        vector_weight: float = 1.0
    ) -> list[tuple[str, float]]:
        """
        Объединение результатов FTS и векторного поиска через RRF.

        Args:
            fts_results: Результаты Full-Text Search [(trade_name, score), ...]
            vector_results: Результаты векторного поиска [(trade_name, distance), ...]
            fts_weight: Вес для FTS результатов (по умолчанию 10.0 для приоритета точных терминов)
            vector_weight: Вес для векторных результатов (по умолчанию 1.0)

        Returns:
            Список кортежей (trade_name, rrf_score), отсортированных по убыванию score
        """
        scores = {}

        # FTS scores (с весом для приоритета точных терминов)
        for rank, (trade_name, _) in enumerate(fts_results, start=1):
            scores.setdefault(trade_name, 0.0)
            scores[trade_name] += fts_weight / (self.k + rank)

        # Vector scores
        for rank, (trade_name, _) in enumerate(vector_results, start=1):
            scores.setdefault(trade_name, 0.0)
            scores[trade_name] += vector_weight / (self.k + rank)

        # Сортируем по убыванию score
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def merge_multiple(
        self,
        results_list: list[tuple[list[tuple[str, float]], float]],
    ) -> list[tuple[str, float]]:
        """
        Объединение нескольких источников результатов через RRF.

        Args:
            results_list: Список кортежей (results, weight)
                где results = [(trade_name, score), ...]
                и weight - вес этого источника

        Returns:
            Список кортежей (trade_name, rrf_score), отсортированных по убыванию score
        """
        scores = {}

        for results, weight in results_list:
            for rank, (trade_name, _) in enumerate(results, start=1):
                scores.setdefault(trade_name, 0.0)
                scores[trade_name] += weight / (self.k + rank)

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
