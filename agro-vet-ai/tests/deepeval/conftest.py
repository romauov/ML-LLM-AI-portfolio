"""
Pytest конфигурация для DeepEval тестов

Автоматически сохраняет результаты тестов в JSON файлы.
"""
import json
import sys
import pytest
from datetime import datetime
from pathlib import Path

_test_results = []
_output_file = None


def _get_output_file() -> Path:
    """Получить путь к файлу результатов (создаётся один раз за сессию)."""
    global _output_file
    if _output_file is None:
        output_dir = Path(__file__).parent / "results"
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _output_file = output_dir / f"test_results_{timestamp}.json"
    return _output_file


def _save_results():
    """Сохранить текущее состояние результатов в файл."""
    output_file = _get_output_file()

    summary = {
        "total": len(_test_results),
        "passed": sum(1 for r in _test_results if r["status"] == "passed"),
        "failed": sum(1 for r in _test_results if r["status"] == "failed"),
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "platform": sys.platform
    }

    try:
        import deepeval
        summary["deepeval_version"] = deepeval.__version__
    except Exception:
        summary["deepeval_version"] = "unknown"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "tests": _test_results
        }, f, ensure_ascii=False, indent=2)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Перехватываем результаты тестов и сохраняем инкрементально."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        result = {
            "test_name": item.nodeid,
            "status": report.outcome,
            "duration": report.duration,
            "timestamp": datetime.now().isoformat()
        }

        if report.failed:
            result["error"] = str(report.longrepr)

        # Читаем данные из item (были сохранены через request.node)
        if hasattr(item, "_deepeval_metrics"):
            result["metrics"] = item._deepeval_metrics

        if hasattr(item, "_deepeval_input") and hasattr(item, "_deepeval_output"):
            result["input"] = item._deepeval_input
            result["actual_output"] = item._deepeval_output

        _test_results.append(result)
        _save_results()


def pytest_sessionfinish(session, exitstatus):
    """Финальная запись (обновляем summary)."""
    if _test_results:
        _save_results()
        print(f"\n\nResults saved to: {_get_output_file()}")