#!/usr/bin/env python
"""
Ranking evaluation test runner.

Оценивает качество ранжирования чанков по ground truth датасету.
Результаты сохраняются в формате deepeval для просмотра в viewer.

Использование:
    python tests/deepeval/run_ranking_tests.py
    python tests/deepeval/run_ranking_tests.py --config tests/deepeval/test_cases/ranking_config.yaml
    python tests/deepeval/run_ranking_tests.py --query-id 5
"""
import json
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

# Добавляем корень проекта в sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import os
import yaml
from sqlalchemy import create_engine, text

from openai import OpenAI

from app.llm.providers.vsegpt import VseGPTProvider
from app.llm.providers.openrouter import OpenrouterProvider
from app.utils.settings import secrets as s
from tests.deepeval.utils.custom_metrics.ranking_metrics import compute_all_metrics


def build_test_db_url() -> str:
    """
    URL для подключения к БД из хост-машины.
    Использует DB_HOST_OVERRIDE / DB_PORT_OVERRIDE из env,
    иначе localhost и db_port_host из .env.
    """
    host = os.environ.get("DB_HOST_OVERRIDE", "localhost")
    port = os.environ.get("DB_PORT_OVERRIDE", str(s.db_port_host))
    return (
        f"postgresql+psycopg://{s.postgres_user}:{s.postgres_password}"
        f"@{host}:{port}/{s.postgres_db}"
    )


class RankingTestRunner:
    """Runner для оценки ranking качества."""

    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.engine = create_engine(build_test_db_url())

        # Параметры из конфига
        ret = self.config["ranking"]
        self.table = ret["table"]
        self.embedding_column = ret["embedding_column"]
        self.doc_limit = ret["doc_limit"]
        self.similarity_threshold = ret["similarity_threshold"]

        emb = self.config["embedding"]
        self.query_instruction = emb.get("query_instruction")  # опциональный prefix для запросов

        # Если задана секция providers — разрешаем активного провайдера
        if "providers" in emb:
            active = emb["active_provider"]
            provider_cfg = emb["providers"][active]
            provider_name = active
        else:
            provider_cfg = emb
            provider_name = emb.get("provider", "vsegpt")

        self.embedding_model = provider_cfg["model"]

        # Источник эмбеддингов: lmstudio > LLMProvider
        if provider_name == "lmstudio":
            self._lmstudio = OpenAI(base_url=provider_cfg["base_url"], api_key="lm-studio")
            self._lmstudio_model = provider_cfg["model"]
            self._direct_provider = None
            print(f"Провайдер: LM Studio ({provider_cfg['base_url']}, модель: {provider_cfg['model']})")
        elif provider_name == "openrouter":
            self._lmstudio = None
            self._direct_provider = OpenrouterProvider(
                api_key=s.openrouter_api_key, base_url=s.openrouter_base_url
            )
            print(f"Провайдер: OpenRouter, модель: {provider_cfg['model']}")
        else:  # vsegpt (default)
            self._lmstudio = None
            self._direct_provider = VseGPTProvider(
                api_key=s.vsegpt_api_key, base_url=s.vsegpt_base_url
            )
            print(f"Провайдер: VseGPT, модель: {provider_cfg['model']}")

        self.thresholds = self.config["metrics_thresholds"]

        # Результаты
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = self.results_dir / f"test_results_{self.timestamp}.json"
        self.test_results = []

    def _vectorize(self, query: str) -> list[float]:
        """Возвращает эмбеддинг через LM Studio или LLMProvider."""
        input_text = f"{self.query_instruction}\nQuery: {query}" if self.query_instruction else query
        if self._lmstudio is not None:
            response = self._lmstudio.embeddings.create(model=self._lmstudio_model, input=input_text)
            return response.data[0].embedding
        return self._direct_provider.vectorize(query=input_text, model=self.embedding_model)

    def _search(self, embedding: list[float]) -> list[int]:
        """Поиск ближайших чанков по embedding, возвращает список ID."""
        # Используем безопасное имя столбца (проверяем на допустимые символы)
        col = self.embedding_column
        if not all(c.isalnum() or c == '_' for c in col):
            raise ValueError(f"Недопустимое имя столбца: {col}")

        sql = text(f"""
            SELECT kbc.id
            FROM {self.table} kbc
            WHERE kbc.{col} IS NOT NULL
              AND kbc.{col} <=> :embedding <= :threshold
            ORDER BY kbc.{col} <=> :embedding ASC
            LIMIT :limit
        """)

        with self.engine.connect() as conn:
            rows = conn.execute(sql, parameters={
                "embedding": str(embedding),
                "threshold": self.similarity_threshold,
                "limit": self.doc_limit,
            }).fetchall()

        return [row.id for row in rows]

    def _save_results(self):
        """Сохранить текущее состояние результатов в файл."""
        passed = sum(1 for r in self.test_results if r["status"] == "passed")
        failed = sum(1 for r in self.test_results if r["status"] == "failed")

        output = {
            "summary": {
                "total": len(self.test_results),
                "passed": passed,
                "failed": failed,
                "timestamp": datetime.now().isoformat(),
                "python_version": sys.version,
                "platform": sys.platform,
                "deepeval_version": "ranking-eval-1.0",
            },
            "tests": self.test_results,
        }

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

    def run_single(self, query_entry: dict, index: int) -> dict:
        """Запустить один тестовый кейс."""
        query = query_entry["query"]
        relevant_ids = query_entry["relevant_ids"]
        relevance_grades = query_entry.get("relevance_grades")
        description = query_entry.get("description", "")
        query_type = query_entry.get("type", "unknown")

        start = time.time()

        # Векторизация + поиск
        embedding = self._vectorize(query)
        retrieved_ids = self._search(embedding)

        duration = time.time() - start

        # Метрики
        scores = compute_all_metrics(retrieved_ids, relevant_ids, self.doc_limit, relevance_grades)

        # Маппинг префикс метрики -> ключ в thresholds (имена содержат фактическое K)
        metric_prefix_to_threshold_key = {
            "Precision@": "precision_at_k",
            "Recall@": "recall_at_k",
            "RR": "mrr",       # per-query RR, порог из mrr
            "nDCG@": "ndcg_at_k",
        }

        def _threshold_key(name: str) -> str | None:
            for prefix, key in metric_prefix_to_threshold_key.items():
                if name.startswith(prefix):
                    return key
            return None

        # Показываем только метрики, у которых есть порог в конфиге
        metrics_data = []
        all_passed = True
        for metric_name, score in scores.items():
            threshold_key = _threshold_key(metric_name)
            if threshold_key not in self.thresholds:
                continue  # метрика не включена в конфиг — пропускаем
            threshold = self.thresholds[threshold_key]
            success = score >= threshold
            if not success:
                all_passed = False

            metrics_data.append({
                "name": metric_name,
                "score": round(score, 4),
                "threshold": threshold,
                "success": success,
                "reason": f"Retrieved IDs: {retrieved_ids} | Relevant IDs: {relevant_ids}",
                "evaluation_steps": None,
            })

        test_name = (
            f"ranking_evaluation::query_{index}"
            f"[{query_type}|{query_entry.get('language', '?')}]"
        )

        result = {
            "test_name": test_name,
            "status": "passed" if all_passed else "failed",
            "duration": round(duration, 2),
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics_data,
            "input": query,
            "actual_output": (
                f"Retrieved: {retrieved_ids}\n"
                f"Expected: {relevant_ids}\n"
                f"Description: {description}"
            ),
        }

        return result

    def run(self, query_index: int = None):
        """Запустить все или один тест."""
        # Загрузка датасета
        dataset_path = project_root / self.config["dataset"]
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        if query_index is not None:
            dataset = [dataset[query_index]]
            indices = [query_index]
        else:
            indices = list(range(len(dataset)))

        config_info = (
            f"table={self.table}, column={self.embedding_column}, "
            f"model={self.embedding_model}, "
            f"threshold={self.similarity_threshold}, K={self.doc_limit}"
        )
        print("=" * 80)
        print("Ranking Evaluation Test")
        print("=" * 80)
        print(f"Config: {config_info}")
        print(f"Dataset: {dataset_path} ({len(dataset)} queries)")
        print(f"Results: {self.output_file}")
        print("=" * 80)
        print()

        for i, (idx, entry) in enumerate(zip(indices, dataset)):
            prefix = f"[{i + 1}/{len(dataset)}]"
            try:
                result = self.run_single(entry, idx)
                status = "PASS" if result["status"] == "passed" else "FAIL"
                scores_str = " | ".join(
                    f"{m['name']}={m['score']:.2f}" for m in result["metrics"]
                )
                print(f"  {prefix} {status}  {entry['query'][:60]}...")
                print(f"         {scores_str}")
            except Exception as e:
                result = {
                    "test_name": f"ranking_evaluation::query_{idx}",
                    "status": "failed",
                    "duration": 0,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "metrics": [],
                    "input": entry["query"],
                    "actual_output": f"Error: {e}",
                }
                print(f"  {prefix} ERROR  {entry['query'][:60]}...")
                print(f"         {e}")

            self.test_results.append(result)
            self._save_results()  # Инкрементальная запись после каждого кейса

        # Итоги
        passed = sum(1 for r in self.test_results if r["status"] == "passed")
        total = len(self.test_results)

        # MRR = среднее RR по всей выборке
        rr_values = [
            m["score"]
            for r in self.test_results
            for m in r.get("metrics", [])
            if m["name"] == "RR"
        ]
        mrr_score = sum(rr_values) / len(rr_values) if rr_values else 0.0

        # Средние значения остальных метрик
        metric_names = [m["name"] for m in (self.test_results[0].get("metrics", []) if self.test_results else [])]
        avg_scores = {}
        for name in metric_names:
            vals = [m["score"] for r in self.test_results for m in r.get("metrics", []) if m["name"] == name]
            avg_scores[name] = sum(vals) / len(vals) if vals else 0.0

        print()
        print("=" * 80)
        print(f"Done: {passed}/{total} passed")
        if avg_scores:
            avg_str = " | ".join(f"{n}={v:.3f}" for n, v in avg_scores.items() if n != "RR")
            print(f"Avg:  {avg_str} | MRR={mrr_score:.3f}")
        print(f"Results: {self.output_file}")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Ranking evaluation test runner")
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=str(Path(__file__).parent / "test_cases" / "ranking_config.yaml"),
        help="Путь к конфигу (по умолчанию tests/deepeval/test_cases/ranking_config.yaml)",
    )
    parser.add_argument(
        "--query-id", "-q",
        type=int,
        default=None,
        help="Индекс конкретного запроса для запуска (0-based)",
    )
    args = parser.parse_args()

    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    runner = RankingTestRunner(args.config)
    runner.run(query_index=args.query_id)


if __name__ == "__main__":
    main()
