"""
Pytest runner для DeepEval тестов
"""
import sys
import pytest
import requests
from pathlib import Path
from deepeval.test_case import LLMTestCase
from dotenv import load_dotenv

# Добавляем корневую директорию проекта в sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.deepeval.utils.test_loader import TestCaseLoader
from tests.deepeval.utils.metrics_factory import MetricsFactory
# НЕ импортируем conftest напрямую - это создает дубликат модуля!
# from tests.deepeval.conftest import store_metrics, store_test_case
from app.utils.settings import secrets as s

load_dotenv()


class TestRunner:
    """
    Runner для выполнения DeepEval тестов

    Загружает тестовые кейсы из YAML и выполняет их с заданными метриками.
    """

    @staticmethod
    def run_test_case(
        test_case_config: dict,
        metrics_config: dict,
        test_id: str,
        request=None
    ):
        """
        Выполнить один тестовый кейс

        Args:
            test_case_config: Конфигурация тестового кейса
            metrics_config: Конфигурация метрик
            test_id: ID теста
        """
        query = test_case_config["query"]


        # Используем эндпоинт /api/submit_json
        api_url = "http://localhost:81/api/submit_json"
        api_key = s.api_key or "your-api-key"

        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {"message": query}

        try:
            api_response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=120
            )
            api_response.raise_for_status()
            response_data = api_response.json()

            # submit_json возвращает {"response": str, "context": str}
            context_str = response_data.get("context", "").strip()
            response = {
                "output": response_data.get("response", ""),
                "context": [context_str] if context_str else []
            }
        except Exception as e:
            error_msg = f"Ошибка при запросе к VetBot API: {str(e)}"
            raise RuntimeError(error_msg)

        # Создаем тестовый кейс для DeepEval
        test_case = LLMTestCase(
            input=query,
            actual_output=response["output"],
            retrieval_context=response["context"] if response["context"] else None
        )

        # Создаем метрики
        has_context = bool(response["context"])

        metrics = MetricsFactory.create_metrics_from_config(
            test_case=test_case_config,
            metrics_config=metrics_config,
            has_context=has_context
        )

        for metric in metrics:
            metric.measure(test_case)

        # Собираем данные метрик
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                "name": metric.__class__.__name__,
                "score": metric.score,
                "threshold": metric.threshold,
                "success": metric.is_successful(),
                "reason": getattr(metric, "reason", None),
                "evaluation_steps": getattr(metric, "evaluation_steps", None)
            })

        # Сохраняем данные в request.node (доступен из conftest.py)
        if request:
            request.node._deepeval_metrics = metrics_data
            request.node._deepeval_input = query
            request.node._deepeval_output = response["output"]

        # Проверяем результаты метрик
        failed_metrics = [m for m in metrics if not m.is_successful()]
        if failed_metrics:
            failed_str = ", ".join([
                f"{m.__class__.__name__} (score: {m.score}, threshold: {m.threshold})"
                for m in failed_metrics
            ])
            raise AssertionError(f"Metrics failed: {failed_str}")


# Загружаем все тесты из YAML файлов
all_test_data = []
all_modules = TestCaseLoader.load_all_test_cases()

for module_name, test_cases in all_modules.items():
    for test_case in test_cases:
        all_test_data.append((test_case, test_case["_metrics_config"]))

test_ids = [f"{tc['_module']}::{tc['id']}" for tc, _ in all_test_data]


@pytest.mark.parametrize(
    "test_case_config,metrics_config",
    all_test_data,
    ids=test_ids
)
def test_evaluation(test_case_config, metrics_config, request):
    """
    Универсальный тест для всех модулей

    Динамически загружает тесты из всех YAML файлов в test_cases/
    и выполняет их с заданными метриками.
    """
    # используем request.node.nodeid (полный путь pytest)
    TestRunner.run_test_case(
        test_case_config=test_case_config,
        metrics_config=metrics_config,
        test_id=request.node.nodeid,
        request=request  # Передаем request для сохранения данных
    )