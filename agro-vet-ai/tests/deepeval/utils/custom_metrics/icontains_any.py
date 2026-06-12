"""
IContainsAny Metric

Case-insensitive metric that checks if the actual output contains at least one
of the expected strings.
"""

from typing import List, Optional
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase


class IContainsAnyMetric(BaseMetric):
    """
    Метрика для проверки наличия хотя бы одной подстроки (без учета регистра)

    Проверяет, содержит ли actual_output хотя бы одну из ожидаемых подстрок.
    Сравнение выполняется без учета регистра (case-insensitive).

    Args:
        expected_strings: Список строк, хотя бы одна из которых должна присутствовать
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
            threshold: Порог успешности (по умолчанию 1.0 = хотя бы одна найдена)
            strict_mode: Строгий режим DeepEval (по умолчанию True)
        """
        self.expected_strings = expected_strings
        self.threshold = threshold
        self.strict_mode = strict_mode

        self.score: Optional[float] = None
        self.success: Optional[bool] = None
        self.reason: Optional[str] = None
        self.found_strings: List[str] = []

    def measure(self, test_case: LLMTestCase) -> float:
        """
        Выполнить проверку

        Args:
            test_case: Тестовый кейс с actual_output

        Returns:
            Оценка: 1.0 если хотя бы одна строка найдена, иначе 0.0
        """
        actual_output = test_case.actual_output

        if not actual_output:
            self.score = 0.0
            self.success = False
            self.reason = "Actual output is empty"
            return self.score

        # Приводим actual_output к нижнему регистру для сравнения
        actual_lower = actual_output.lower()

        # Ищем каждую строку
        self.found_strings = []
        for expected in self.expected_strings:
            if expected.lower() in actual_lower:
                self.found_strings.append(expected)

        # Оценка: 1.0 если найдена хотя бы одна, иначе 0.0
        if self.found_strings:
            self.score = 1.0
            self.success = self.score >= self.threshold
            self.reason = f"Found {len(self.found_strings)} of {len(self.expected_strings)} expected strings: {', '.join(self.found_strings)}"
        else:
            self.score = 0.0
            self.success = False
            self.reason = f"None of the expected strings found in output. Expected any of: {', '.join(self.expected_strings)}"

        return self.score

    def is_successful(self) -> bool:
        """
        Проверка успешности теста

        Returns:
            True если найдена хотя бы одна подстрока
        """
        if self.success is None:
            raise ValueError(
                "Metric has not been measured yet. Call measure() first."
            )
        return self.success

    @property
    def __name__(self) -> str:
        """Имя метрики для отображения"""
        return "IContainsAny"
