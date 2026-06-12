"""
IContainsAll Metric

Case-insensitive metric that checks if the actual output contains ALL
of the expected strings.
"""

from typing import List, Optional
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase


class IContainsAllMetric(BaseMetric):
    """
    Метрика для проверки наличия всех подстрок (без учета регистра)

    Проверяет, содержит ли actual_output все ожидаемые подстроки.
    Сравнение выполняется без учета регистра (case-insensitive).

    Args:
        expected_strings: Список строк, все из которых должны присутствовать
    """

    def __init__(
        self,
        expected_strings: List[str],
        threshold: float = 1.0,
        strict_mode: bool = True
    ):
        """
        Инициализация метрики

        Args:
            expected_strings: Список строк для поиска (case-insensitive)
            threshold: Порог успешности (по умолчанию 1.0 = все найдены)
            strict_mode: Строгий режим DeepEval (по умолчанию True)
        """
        self.expected_strings = expected_strings
        self.threshold = threshold
        self.strict_mode = strict_mode

        self.score: Optional[float] = None
        self.success: Optional[bool] = None
        self.reason: Optional[str] = None
        self.found_strings: List[str] = []
        self.missing_strings: List[str] = []

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Выполнить проверку

        Args:
            test_case: Тестовый кейс с actual_output

        Returns:
            Оценка: доля найденных строк (1.0 если все найдены)
        """
        actual_output = test_case.actual_output

        if not actual_output:
            self.score = 0.0
            self.success = False
            self.missing_strings = list(self.expected_strings)
            self.reason = "Actual output is empty"
            return self.score

        actual_lower = actual_output.lower()

        self.found_strings = []
        self.missing_strings = []
        for expected in self.expected_strings:
            if expected.lower() in actual_lower:
                self.found_strings.append(expected)
            else:
                self.missing_strings.append(expected)

        self.score = len(self.found_strings) / len(self.expected_strings) if self.expected_strings else 0.0
        self.success = self.score >= self.threshold

        if self.missing_strings:
            self.reason = (
                f"Found {len(self.found_strings)} of {len(self.expected_strings)} expected strings. "
                f"Missing: {', '.join(self.missing_strings)}"
            )
        else:
            self.reason = f"All {len(self.expected_strings)} expected strings found: {', '.join(self.found_strings)}"

        return self.score

    def is_successful(self) -> bool:
        """
        Проверка успешности теста

        Returns:
            True если все подстроки найдены (или score >= threshold)
        """
        if self.success is None:
            raise ValueError(
                "Metric has not been measured yet. Call measure() first."
            )
        return self.success

    @property
    def __name__(self) -> str:
        """Имя метрики для отображения"""
        return "IContainsAll"
