#!/usr/bin/env python
"""
CLI для запуска DeepEval тестов

Удобный интерфейс для запуска тестов с различными опциями.
"""
import sys
import pytest
import argparse
from pathlib import Path


def main():
    """Главная функция CLI"""
    # Создаём папку results, если её нет
    script_dir = Path(__file__).parent
    results_dir = script_dir / "results"
    results_dir.mkdir(exist_ok=True)

    parser = argparse.ArgumentParser(
        description="Запуск DeepEval тестов для Vet-RAG-System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Запустить все тесты
  python run_tests.py

  # Запустить тесты из конкретного файла
  python run_tests.py --file test_cases/drugs_instructions_local.yaml

  # Запустить конкретный тест из файла
  python run_tests.py --file test_cases/drugs_instructions.yaml --test drug_description_pulmosol

  # С кратким указанием файла и теста
  python run_tests.py -f test_cases/drugs_instructions.yaml -t drug_full_instruction

  # Подробный вывод
  python run_tests.py -v

  # Остановиться после первой ошибки
  python run_tests.py -x

  # Комбинация опций
  python run_tests.py -f test_cases/drugs_instructions.yaml -t drug_search_by_animal -v -x
        """
    )


    parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="Запустить тесты из конкретного YAML файла (например, test_cases/drugs_instructions_local.yaml)"
    )

    parser.add_argument(
        "--test",
        "-t",
        type=str,
        help="Запустить конкретный тест по ID (требует указания --file)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Подробный вывод"
    )

    parser.add_argument(
        "--stop-on-first",
        "-x",
        action="store_true",
        help="Остановиться после первой ошибки"
    )

    args = parser.parse_args()

    # Валидация: --test требует --file
    if args.test and not args.file:
        print("Ошибка: опция --test требует указания --file")
        print("Пример: python run_tests.py --file test_cases/drugs_instructions.yaml --test drug_description_pulmosol")
        sys.exit(1)

    # Определяем путь к test_runner.py относительно этого файла
    test_runner_path = script_dir / "utils" / "test_runner.py"

    pytest_args = [str(test_runner_path)]

    if args.file:
        # Если путь относительный, делаем его относительно текущей директории или script_dir
        file_path = Path(args.file)
        if not file_path.is_absolute():
            # Пробуем найти файл относительно текущей директории
            if not file_path.exists():
                # Если не нашли, пробуем относительно директории скрипта
                file_path = script_dir / args.file

        if not file_path.exists():
            print(f"Ошибка: файл не найден: {args.file}")
            sys.exit(1)

        # Импортируем TestCaseLoader относительно текущего файла
        sys.path.insert(0, str(script_dir))
        from utils.test_loader import TestCaseLoader
        config = TestCaseLoader.load_yaml(str(file_path))
        module_info = TestCaseLoader.get_module_info(config, str(file_path))
        module_name = module_info["module"]

        # Если указан конкретный тест, проверяем его существование
        if args.test:
            test_cases = TestCaseLoader.get_test_cases(config)
            test_ids = [tc.get("id") for tc in test_cases]

            if args.test not in test_ids:
                print(f"Ошибка: тест с ID '{args.test}' не найден в файле {args.file}")
                print(f"\nДоступные тесты в этом файле:")
                for test_case in test_cases:
                    test_id = test_case.get("id", "unknown")
                    description = test_case.get("description", "")
                    print(f"  - {test_id}: {description}")
                sys.exit(1)

            # Используем комбинацию module и test_id для точного поиска
            pytest_args.extend(["-k", f"{module_name} and {args.test}"])
        else:
            pytest_args.extend(["-k", module_name])

    if args.verbose:
        pytest_args.append("-v")

    if args.stop_on_first:
        pytest_args.append("-x")

    print("=" * 80)
    print("DeepEval Tests for Vet-RAG-System")
    print("=" * 80)
    print(f"Command: pytest {' '.join(pytest_args)}")
    print("=" * 80)
    print()

    sys.exit(pytest.main(pytest_args))


if __name__ == "__main__":
    main()