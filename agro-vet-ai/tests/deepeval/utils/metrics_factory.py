"""
Фабрика для создания DeepEval метрик

Предоставляет унифицированный интерфейс для создания метрик с различными провайдерами.
"""
import sys
from pathlib import Path
from typing import List, Dict, Any
from deepeval.metrics import GEval, AnswerRelevancyMetric, FaithfulnessMetric, BaseMetric
from deepeval.test_case import LLMTestCaseParams

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.deepeval.utils.providers import ProviderFactory
from tests.deepeval.utils.custom_metrics import IContainsAnyMetric, IContainsAllMetric


class MetricsFactory:
    """
    Фабрика для создания DeepEval метрик

    Создает метрики с нужными провайдерами на основе конфигурации из YAML.

    Examples:
        >>> config = {"provider": "deepseek", "threshold": 0.7}
        >>> metric = MetricsFactory.create_geval(
        ...     criteria=["Точность", "Полнота"],
        ...     provider_config=config
        ... )

        >>> metrics = MetricsFactory.create_metrics_from_config(
        ...     test_case={"expected_criteria": ["Критерий 1"]},
        ...     metrics_config={...}
        ... )
    """

    @staticmethod
    def create_geval(
        criteria: List[str],
        provider_config: Dict[str, Any]
    ) -> GEval:
        """
        Создать GEval метрику

        Args:
            criteria: Список критериев оценки
            provider_config: Конфигурация провайдера с ключами:
                - provider: тип провайдера (deepseek, vsegpt, openrouter, local)
                - model: название модели (опционально)
                - threshold: порог успешности (по умолчанию 0.7)

        Returns:
            Настроенная GEval метрика

        Examples:
            >>> config = {
            ...     "provider": "deepseek",
            ...     "model": "deepseek-chat",
            ...     "threshold": 0.7
            ... }
            >>> metric = MetricsFactory.create_geval(
            ...     criteria=["Точность ответа", "Полнота информации"],
            ...     provider_config=config
            ... )
        """
        criteria_text = "\n".join([f"- {criterion}" for criterion in criteria])

        threshold = provider_config.get("threshold", 0.7)
        provider = ProviderFactory.from_config(provider_config)

        return GEval(
            name="Quality",
            criteria=f"Оцените качество ответа по следующим критериям:\n{criteria_text}",
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            threshold=threshold,
            model=provider
        )

    @staticmethod
    def create_answer_relevancy(provider_config: Dict[str, Any]) -> AnswerRelevancyMetric:
        """
        Создать AnswerRelevancyMetric

        Args:
            provider_config: Конфигурация провайдера с ключами:
                - provider: тип провайдера
                - model: название модели (опционально)
                - threshold: порог успешности (по умолчанию 0.7)

        Returns:
            Настроенная AnswerRelevancyMetric

        Examples:
            >>> config = {"provider": "deepseek", "threshold": 0.7}
            >>> metric = MetricsFactory.create_answer_relevancy(config)
        """
        threshold = provider_config.get("threshold", 0.7)
        provider = ProviderFactory.from_config(provider_config)

        return AnswerRelevancyMetric(
            threshold=threshold,
            model=provider
        )

    @staticmethod
    def create_faithfulness(provider_config: Dict[str, Any]) -> FaithfulnessMetric:
        """
        Создать FaithfulnessMetric

        Args:
            provider_config: Конфигурация провайдера с ключами:
                - provider: тип провайдера
                - model: название модели (опционально)
                - threshold: порог успешности (по умолчанию 0.5)

        Returns:
            Настроенная FaithfulnessMetric

        Examples:
            >>> config = {"provider": "deepseek", "threshold": 0.5}
            >>> metric = MetricsFactory.create_faithfulness(config)
        """
        threshold = provider_config.get("threshold", 0.5)
        provider = ProviderFactory.from_config(provider_config)

        return FaithfulnessMetric(
            threshold=threshold,
            model=provider
        )

    @staticmethod
    def create_icontains_any(
        expected_strings: List[str],
        threshold: float = 1.0
    ) -> IContainsAnyMetric:
        """
        Создать IContainsAnyMetric

        Args:
            expected_strings: Список строк, хотя бы одна из которых должна
                присутствовать в ответе (case-insensitive)
            threshold: Порог успешности (по умолчанию 1.0)

        Returns:
            Настроенная IContainsAnyMetric
        """
        return IContainsAnyMetric(
            expected_strings=expected_strings,
            threshold=threshold
        )

    @staticmethod
    def create_icontains_all(
        expected_strings: List[str],
        threshold: float = 1.0
    ) -> IContainsAllMetric:
        """
        Создать IContainsAllMetric

        Args:
            expected_strings: Список строк, все из которых должны
                присутствовать в ответе (case-insensitive)
            threshold: Порог успешности (по умолчанию 1.0)

        Returns:
            Настроенная IContainsAllMetric
        """
        return IContainsAllMetric(
            expected_strings=expected_strings,
            threshold=threshold
        )

    @staticmethod
    def create_metrics_from_config(
        test_case: Dict[str, Any],
        metrics_config: Dict[str, Any],
        has_context: bool = False
    ) -> List[BaseMetric]:
        """
        Создать все метрики из конфигурации

        Args:
            test_case: Тестовый кейс с ключами:
                - expected_criteria: критерии для GEval
                - expected_strings: строки для IContainsAny
                - expected_strings_all: строки для IContainsAll
            metrics_config: Конфигурация метрик из YAML с ключами:
                - geval_quality: конфиг для GEval
                - answer_relevancy: конфиг для AnswerRelevancyMetric
                - faithfulness: конфиг для FaithfulnessMetric (только если has_context=True)
                - icontains_any: конфиг для IContainsAnyMetric
                - icontains_all: конфиг для IContainsAllMetric
            has_context: Есть ли retrieval context (для Faithfulness)

        Returns:
            Список настроенных метрик
        """
        metrics = []

        # 1. GEval Quality Metric
        if "geval_quality" in metrics_config:
            geval_config = metrics_config["geval_quality"]
            criteria = test_case.get("expected_criteria", [])

            if criteria:
                quality_metric = MetricsFactory.create_geval(
                    criteria=criteria,
                    provider_config=geval_config
                )
                metrics.append(quality_metric)

        # 2. Answer Relevancy Metric
        if "answer_relevancy" in metrics_config:
            relevancy_config = metrics_config["answer_relevancy"]
            relevancy_metric = MetricsFactory.create_answer_relevancy(relevancy_config)
            metrics.append(relevancy_metric)

        # 3. Faithfulness Metric (только если есть контекст)
        if has_context and "faithfulness" in metrics_config:
            faithfulness_config = metrics_config["faithfulness"]
            faithfulness_metric = MetricsFactory.create_faithfulness(faithfulness_config)
            metrics.append(faithfulness_metric)

        # 4. IContainsAny Metric
        if "icontains_any" in metrics_config:
            icontains_config = metrics_config["icontains_any"]
            expected_strings = test_case.get("expected_strings", [])

            if expected_strings:
                threshold = icontains_config.get("threshold", 1.0)
                icontains_metric = MetricsFactory.create_icontains_any(
                    expected_strings=expected_strings,
                    threshold=threshold
                )
                metrics.append(icontains_metric)

        # 5. IContainsAll Metric
        if "icontains_all" in metrics_config:
            icontains_all_config = metrics_config["icontains_all"]
            expected_strings_all = test_case.get("expected_strings_all", [])

            if expected_strings_all:
                threshold = icontains_all_config.get("threshold", 1.0)
                icontains_all_metric = MetricsFactory.create_icontains_all(
                    expected_strings=expected_strings_all,
                    threshold=threshold
                )
                metrics.append(icontains_all_metric)

        return metrics