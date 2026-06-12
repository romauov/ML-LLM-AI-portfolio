"""
Загрузчик тестовых кейсов из YAML файлов

Предоставляет функции для загрузки и валидации тестовых кейсов.
"""
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


class TestCaseLoader:
    """
    Загрузчик тестовых кейсов из YAML

    Загружает тестовые кейсы и конфигурацию метрик из YAML файлов.

    Examples:
        >>> # Загрузить один файл
        >>> config = TestCaseLoader.load_yaml("test_cases/drugs_instructions.yaml")
        >>> test_cases = TestCaseLoader.get_test_cases(config)

        >>> # Найти все файлы с тестами
        >>> files = TestCaseLoader.find_test_case_files()
        >>> for file in files:
        ...     config = TestCaseLoader.load_yaml(file)
        ...     test_cases = TestCaseLoader.get_test_cases(config)
    """

    @staticmethod
    def load_yaml(file_path: str) -> Dict[str, Any]:
        """
        Загрузить YAML файл

        Args:
            file_path: Путь к YAML файлу (абсолютный или относительный)

        Returns:
            Словарь с конфигурацией

        Raises:
            FileNotFoundError: Если файл не найден
            yaml.YAMLError: Если YAML некорректен
        """
        path = Path(file_path)

        if not path.is_absolute():
            base_dir = Path(__file__).parent.parent  # Поднимаемся на уровень выше (из utils в deepeval)
            path = base_dir / file_path

        if not path.exists():
            raise FileNotFoundError(f"YAML файл не найден: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def get_test_cases(config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Получить список тестовых кейсов из конфигурации

        Args:
            config: Словарь конфигурации из YAML

        Returns:
            Список тестовых кейсов
        """
        return config.get("test_cases", [])

    @staticmethod
    def get_metrics_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Получить конфигурацию метрик из конфигурации

        Args:
            config: Словарь конфигурации из YAML

        Returns:
            Конфигурация метрик
        """
        return config.get("metrics_config", {})

    @staticmethod
    def get_module_info(config: Dict[str, Any], source_file: Optional[str] = None) -> Dict[str, str]:
        """
        Получить мета-информацию о модуле

        Args:
            config: Словарь конфигурации из YAML
            source_file: Путь к исходному YAML файлу (для авто-генерации module)

        Returns:
            Словарь с ключами 'module' и 'description'
        """
        module_name = config.get("module")

        # Если module не указан, генерируем из имени файла
        if not module_name and source_file:
            file_path = Path(source_file)
            module_name = file_path.stem  # Имя файла без расширения

        # Если всё ещё нет имени, используем "unknown"
        if not module_name:
            module_name = "unknown"

        return {
            "module": module_name,
            "description": config.get("description", "")
        }

    @staticmethod
    def find_test_case_files(directory: str = "test_cases") -> List[str]:
        """
        Найти все YAML файлы с тестами в директории

        Args:
            directory: Директория для поиска (относительно текущего файла)

        Returns:
            Список путей к YAML файлам
        """
        base_dir = Path(__file__).parent.parent  # Поднимаемся на уровень выше (из utils в deepeval)
        test_cases_dir = base_dir / directory

        if not test_cases_dir.exists():
            return []

        yaml_files = []
        for yaml_file in test_cases_dir.glob("*.yaml"):
            if not yaml_file.name.startswith("_"):
                yaml_files.append(str(yaml_file.relative_to(base_dir)))

        return sorted(yaml_files)

    @staticmethod
    def load_all_test_cases(directory: str = "test_cases") -> Dict[str, List[Dict[str, Any]]]:
        """
        Загрузить все тестовые кейсы из всех YAML файлов

        Args:
            directory: Директория с YAML файлами

        Returns:
            Словарь {module_name: [test_cases]}
        """
        all_tests = {}
        yaml_files = TestCaseLoader.find_test_case_files(directory)

        for yaml_file in yaml_files:
            config = TestCaseLoader.load_yaml(yaml_file)
            module_info = TestCaseLoader.get_module_info(config, yaml_file)
            module_name = module_info["module"]

            test_cases = TestCaseLoader.get_test_cases(config)
            metrics_config = TestCaseLoader.get_metrics_config(config)

            for test_case in test_cases:
                test_case["_module"] = module_name
                test_case["_metrics_config"] = metrics_config
                test_case["_source_file"] = yaml_file

            all_tests[module_name] = test_cases

        return all_tests

    @staticmethod
    def validate_test_case(test_case: Dict[str, Any]) -> bool:
        """
        Валидировать тестовый кейс

        Args:
            test_case: Тестовый кейс для валидации

        Returns:
            True если валиден, иначе False
        """
        required_fields = ["id", "description", "query"]

        for field in required_fields:
            if field not in test_case:
                return False

        return True