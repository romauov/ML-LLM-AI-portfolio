"""
Метрики для оценки качества ranking (IR metrics).

Precision@K, Recall@K, MRR, nDCG@K — вычисляются по ground truth chunk IDs.
"""
import math
from typing import List, Dict, Optional


def precision_at_k(retrieved_ids: List[int], relevant_ids: List[int]) -> float:
    """Доля релевантных среди K возвращённых."""
    if not retrieved_ids:
        return 0.0
    relevant_set = set(relevant_ids)
    hits = sum(1 for rid in retrieved_ids if rid in relevant_set)
    return hits / len(retrieved_ids)


def recall_at_k(retrieved_ids: List[int], relevant_ids: List[int]) -> float:
    """Доля найденных из всех релевантных."""
    if not relevant_ids:
        return 0.0
    relevant_set = set(relevant_ids)
    hits = sum(1 for rid in retrieved_ids if rid in relevant_set)
    return hits / len(relevant_set)


def reciprocal_rank(retrieved_ids: List[int], relevant_ids: List[int]) -> float:
    """Reciprocal Rank (RR) — 1/позиция первого релевантного.
    MRR = среднее RR по всей выборке, считается в runner.
    """
    relevant_set = set(relevant_ids)
    for i, rid in enumerate(retrieved_ids):
        if rid in relevant_set:
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(
    retrieved_ids: List[int],
    relevant_ids: List[int],
    relevance_grades: Optional[Dict[str, int]] = None
) -> float:
    """
    nDCG@K с учётом graded relevance.

    Если relevance_grades не заданы, используется binary relevance (0/1).
    """
    if not retrieved_ids or not relevant_ids:
        return 0.0

    relevant_set = set(relevant_ids)

    def get_grade(chunk_id: int) -> float:
        if relevance_grades:
            return float(relevance_grades.get(str(chunk_id), 0))
        return 1.0 if chunk_id in relevant_set else 0.0

    # DCG
    dcg = 0.0
    for i, rid in enumerate(retrieved_ids):
        rel = get_grade(rid)
        dcg += rel / math.log2(i + 2)  # i+2 потому что log2(1) = 0

    # Ideal DCG: отсортированные по убыванию relevance
    if relevance_grades:
        ideal_grades = sorted(
            [float(relevance_grades.get(str(rid), 0)) for rid in relevant_ids],
            reverse=True
        )
    else:
        ideal_grades = [1.0] * len(relevant_ids)

    idcg = 0.0
    for i, rel in enumerate(ideal_grades[:len(retrieved_ids)]):
        idcg += rel / math.log2(i + 2)

    if idcg == 0:
        return 0.0
    return dcg / idcg


def compute_all_metrics(
    retrieved_ids: List[int],
    relevant_ids: List[int],
    k: int,
    relevance_grades: Optional[Dict[str, int]] = None
) -> Dict[str, float]:
    """Вычислить все метрики

    RR — per-query Reciprocal Rank (для расчёта MRR по выборке в runner).
    """
    retrieved_ids = retrieved_ids[:k]
    return {
        f"Precision@{k}": precision_at_k(retrieved_ids, relevant_ids),
        f"Recall@{k}": recall_at_k(retrieved_ids, relevant_ids),
        "RR": reciprocal_rank(retrieved_ids, relevant_ids),
        f"nDCG@{k}": ndcg_at_k(retrieved_ids, relevant_ids, relevance_grades),
    }