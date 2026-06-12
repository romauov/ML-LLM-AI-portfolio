"""
Модули поискового движка для препаратов.

Структура:
- query_executor.py: SQL-запросы (FTS, vector, metadata)
- fusion.py: Алгоритмы ранжирования (RRF)
- formatters.py: Форматирование результатов (Markdown)
"""

from .query_executor import DrugQueryExecutor
from .fusion import RRFFusion
from .formatters import MarkdownFormatter

__all__ = ['DrugQueryExecutor', 'RRFFusion', 'MarkdownFormatter']
