#!/usr/bin/env python3
"""
Визуализация результатов DeepEval тестов

Запускает HTTP сервер для просмотра результатов тестов в браузере.
"""
import http.server
import socketserver
import os
import sys
import webbrowser
import json
from pathlib import Path
from typing import List


class ResultsViewer:
    """
    Viewer для результатов DeepEval тестов

    Загружает и отображает результаты тестов через HTTP сервер.

    Examples:
        >>> viewer = ResultsViewer()
        >>> viewer.list_results()
        ['test_results_20251212_120000.json', ...]

        >>> viewer.serve(port=8000)
        # Открывает браузер с результатами
    """

    def __init__(self, results_dir: str = None):
        """
        Инициализация viewer

        Args:
            results_dir: Директория с результатами (по умолчанию ./results)
        """
        if results_dir:
            self.results_dir = Path(results_dir)
        else:
            self.results_dir = Path(__file__).parent / "results"

    def list_results(self) -> List[str]:
        """
        Список всех файлов с результатами

        Returns:
            Список имен файлов (sorted по дате, новые первые)

        Examples:
            >>> viewer = ResultsViewer()
            >>> files = viewer.list_results()
            >>> print(files[0])  # Самый свежий файл
            test_results_20251212_120000.json
        """
        if not self.results_dir.exists():
            return []

        json_files = list(self.results_dir.glob("test_results_*.json"))
        return sorted([f.name for f in json_files], reverse=True)

    def load_result(self, filename: str) -> dict:
        """
        Загрузить файл с результатами

        Args:
            filename: Имя файла

        Returns:
            Словарь с результатами

        Examples:
            >>> viewer = ResultsViewer()
            >>> result = viewer.load_result("test_results_20251212_120000.json")
            >>> print(result["summary"]["total"])
            16
        """
        file_path = self.results_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def serve(self, port: int = 8000):
        """
        Запустить HTTP сервер для просмотра результатов

        Args:
            port: Порт (по умолчанию 8000)

        Examples:
            >>> viewer = ResultsViewer()
            >>> viewer.serve(port=8000)
            # Открывается браузер с результатами
        """
        os.chdir(Path(__file__).parent)

        class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def end_headers(self):
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET")
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                super().end_headers()

            def log_message(self, format, *args):
                if args[1] == "200":
                    return
                super().log_message(format, *args)

        try:
            with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
                print("=" * 70)
                print("DeepEval Test Results Viewer")
                print("=" * 70)
                print(f"Сервер запущен: http://localhost:{port}/utils/viewer_templates/viewer.html")
                print("=" * 70)
                print("Нажмите Ctrl+C для остановки")
                print()

                webbrowser.open(f"http://localhost:{port}/utils/viewer_templates/viewer.html")

                httpd.serve_forever()

        except KeyboardInterrupt:
            print("\n\nСервер остановлен")

        except OSError as e:
            if e.errno == 10048 or e.errno == 98:
                print(f"\nОшибка: порт {port} уже используется")
                print(f"Попробуйте открыть http://localhost:{port}/utils/viewer_templates/viewer.html")
                print(f"или измените порт: python viewer.py --port {port + 1}")
            else:
                raise


def start_viewer(port: int = 8000, results_dir: str = None):
    """
    Запустить viewer (удобная функция)

    Args:
        port: Порт для HTTP сервера
        results_dir: Директория с результатами

    Examples:
        >>> from viewer import start_viewer
        >>> start_viewer(port=8000)
    """
    viewer = ResultsViewer(results_dir=results_dir)
    viewer.serve(port=port)


def main():
    """CLI для запуска viewer"""
    import argparse

    parser = argparse.ArgumentParser(description="Просмотр результатов DeepEval тестов")
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Порт для HTTP сервера (по умолчанию 8000)"
    )
    parser.add_argument(
        "--results-dir",
        "-d",
        type=str,
        help="Директория с результатами"
    )

    args = parser.parse_args()

    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except:
            pass

    start_viewer(port=args.port, results_dir=args.results_dir)


if __name__ == "__main__":
    main()