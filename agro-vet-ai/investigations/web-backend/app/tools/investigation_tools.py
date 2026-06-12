"""Async Langchain Tools for investigation file operations."""

import asyncio
import logging

from langchain_core.tools import BaseTool
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, Type, List
from app.services.investigation_manager import InvestigationManager


logger = logging.getLogger(__name__)


class CreateInvestigationInput(BaseModel):
    """Input schema for CreateInvestigationTool."""

    farm_name: str = Field(
        ...,
        description="Name of the farm where the incident occurred"
    )
    animal_type: str = Field(
        ...,
        description=(
            "Type of animals affected (e.g., 'pigs', 'poultry', 'piglets', 'broilers')"
        )
    )
    problem_type: str = Field(
        ...,
        description=(
            "Type of problem/disease (e.g., 'diarrhea', 'respiratory', 'mortality'). "
            "This will be used in the investigation folder name."
        )
    )
    description: str = Field(
        ...,
        description=(
            "Initial description of the incident provided by the user. "
            "Include all available information: symptoms, timeline, affected animals count, etc."
        )
    )


class CreateInvestigationTool(BaseTool):
    """
    Tool to create a new veterinary investigation with structured files.

    Use this tool at the very beginning when a user reports a new incident or outbreak.
    This creates a dedicated investigation directory with template files for systematic
    evidence collection and hypothesis tracking.

    **What it creates:**
    - Investigation directory: YYYYMMDD_farm-name_problem/
    - STATUS.md: Investigation progress tracker
    - 00_incident.md: Initial incident description
    - 01_group_card.md: Template for animal group information

    **When to use:**
    - User reports a new disease outbreak or health problem
    - Starting a fresh investigation case
    - User asks to "start a new investigation" or "investigate a problem"

    **When NOT to use:**
    - When continuing an existing investigation (use other file tools instead)
    - For general questions not related to a specific case

    After creating an investigation, use write_file and other tools to populate
    the investigation files with collected data and analysis.
    """

    name: str = "create_investigation"
    description: str = (
        "Creates a new veterinary investigation with a unique directory and initial template files. "
        "Use this at the start of every new case/outbreak investigation. "
        "Returns the investigation ID for use with other file operations."
    )
    args_schema: Type[BaseModel] = CreateInvestigationInput

    investigation_manager: InvestigationManager

    def __init__(self, investigation_manager: InvestigationManager):
        super().__init__(investigation_manager=investigation_manager)

    def _run(
        self,
        farm_name: str,
        animal_type: str,
        problem_type: str,
        description: str
    ) -> str:
        """Create new investigation."""
        investigation = asyncio.run(self.investigation_manager.create_investigation(
            farm_name=farm_name,
            animal_type=animal_type,
            problem_type=problem_type,
            description=description
        ))
        return (
            f"Successfully created investigation: {investigation.id}\n"
            f"Path: {investigation.path}\n"
            f"Farm: {investigation.farm_name}\n"
            f"Animal Type: {investigation.animal_type}\n"
            f"Problem: {investigation.problem_type}\n\n"
            f"Initial files created:\n"
            f"- STATUS.md: Investigation progress tracker\n"
            f"- 00_incident.md: Initial incident description\n"
            f"- 01_group_card.md: Animal group information template\n\n"
            f"Use write_file or other file tools with investigation_id='{investigation.id}' "
            f"to add more files and update the investigation."
        )


class ListFilesInput(BaseModel):
    """Схема входных данных для ListFilesTool."""

    investigation_id: Optional[str] = Field(
        default="",
        description="ID расследования (автоматически добавляется бэкендом, не указывать)"
    )


class ListFilesTool(BaseTool):
    """
    Инструмент для получения списка файлов в папке расследования.

    Используй этот инструмент чтобы:
    - Увидеть какие файлы существуют в расследовании
    - Проверить какие данные уже собраны
    - Найти конкретное имя файла перед его чтением
    - Проверить создание файла после операции записи

    Возвращает отсортированный список имен файлов в папке расследования.

    **Лучшие практики:**
    - Используй перед чтением файлов чтобы убедиться что они существуют
    - Используй чтобы понять структуру расследования
    - Полезен когда пользователь спрашивает "какие файлы у нас есть?"
    """

    name: str = "list_files"
    description: str = (
        "Показывает список всех файлов в папке текущего расследования. "
        "Возвращает только имена файлов (без содержимого). Используй read_file для просмотра содержимого."
    )
    args_schema: Type[BaseModel] = ListFilesInput

    investigation_manager: InvestigationManager

    def __init__(self, investigation_manager: InvestigationManager):
        super().__init__(investigation_manager=investigation_manager)

    def _run(self, investigation_id: str = "") -> str:
        """Список файлов в расследовании."""
        files = asyncio.run(
            self.investigation_manager.list_files(investigation_id))

        if not files:
            return "Файлы не найдены"

        result = "Файлы:\n"
        for filename in files:
            result += f"- {filename}\n"

        return result


class ReadFileInput(BaseModel):
    """Схема входных данных для ReadFileTool."""

    investigation_id: Optional[str] = Field(
        default="",
        description="ID расследования (автоматически добавляется бэкендом, не указывать)"
    )
    filename: str = Field(
        ...,
        description=(
            "Имя файла для чтения (например, '00_incident.md', 'STATUS.md'). "
            "Используйте list_files для просмотра доступных файлов."
        )
    )


class ReadFileTool(BaseTool):
    """
    Инструмент для чтения содержимого файла из расследования.

    Используй этот инструмент чтобы:
    - Просмотреть существующие данные расследования
    - Проверить какая информация уже собрана
    - Прочитать описания инцидента, карты группы, результаты лабораторных анализов
    - Просмотреть предыдущие гипотезы перед их обновлением
    - Проверить текущий STATUS перед его обновлением

    Возвращает полное содержимое файла как текст.

    **Лучшие практики:**
    - Всегда читай STATUS.md в начале сессии
    - Читай существующие файлы гипотез перед добавлением новых
    - Читай 00_incident.md чтобы понять предысторию случая
    - Проверяй содержимое файла после операций записи
    """

    name: str = "read_file"
    description: str = (
        "Читает и возвращает полное содержимое файла из папки расследования. "
        "Используй для просмотра существующих данных, гипотез, лабораторных результатов или любого файла расследования."
    )
    args_schema: Type[BaseModel] = ReadFileInput

    investigation_manager: InvestigationManager

    def __init__(self, investigation_manager: InvestigationManager):
        super().__init__(investigation_manager=investigation_manager)

    def _run(self, filename: str, investigation_id: str = "") -> str:
        """Чтение содержимого файла."""
        try:
            content = asyncio.run(
                self.investigation_manager.read_file(investigation_id, filename))
            return content
        except FileNotFoundError as e:
            return f"Ошибка: {str(e)}"


class WriteFileInput(BaseModel):
    """Схема входных данных для WriteFileTool."""

    investigation_id: Optional[str] = Field(
        default="",
        description="ID расследования (автоматически добавляется бэкендом, не указывать)"
    )
    filename: str = Field(
        ...,
        description=(
            "Имя файла для записи (например, '02_lab_results.md', '03_hypotheses.md'). "
            "Используйте описательные имена. Файлы нумеруются: 00_, 01_, 02_, и т.д."
        )
    )
    content: str = Field(
        ...,
        description=(
            "Полное содержимое для записи в файл. "
            "Используйте корректное форматирование Markdown. Включайте заголовки, списки, таблицы по необходимости. "
            "Для файлов с гипотезами всегда указывайте источники (книга, номера страниц)."
        )
    )


class WriteFileTool(BaseTool):
    """
    Инструмент для записи (создания или перезаписи) файла в расследовании.

    Используй этот инструмент чтобы:
    - Создавать новые файлы расследования (лабораторные результаты, гипотезы, выводы)
    - Обновлять существующие файлы новой информацией
    - Документировать находки с правильной структурой и цитированием источников

    **Важные замечания:**
    - Этот инструмент ПЕРЕЗАПИСЫВАЕТ файл если он существует
    - Используй read_file сначала если хочешь добавить/изменить существующее содержимое
    - Всегда используй форматирование Markdown
    - Всегда цитируй источники из базы знаний (книга, страница)

    **Соглашения по именам файлов:**
    - 00_incident.md: Начальный инцидент (создается автоматически)
    - 01_group_card.md: Данные группы животных (создается автоматически)
    - 02_*.md: Дополнительные файлы данных
    - 03_*.md: Файлы анализа
    - 04_*.md: Гипотезы
    - 05_*.md: Выводы/отчеты
    - STATUS.md: Отслеживание прогресса (создается автоматически)

    **Лучшие практики:**
    - Читай файл сначала если он существует и ты хочешь сохранить содержимое
    - Используй описательные имена файлов
    - Включай цитирование источников в файлы гипотез/анализа
    - Используй правильное форматирование Markdown для читабельности
    """

    name: str = "write_file"
    description: str = (
        "Записывает содержимое в файл в папке расследования. "
        "Создает новый файл или перезаписывает существующий. "
        "Используй форматирование Markdown и всегда цитируй источники из базы знаний."
    )
    args_schema: Type[BaseModel] = WriteFileInput

    investigation_manager: InvestigationManager

    def __init__(self, investigation_manager: InvestigationManager):
        super().__init__(investigation_manager=investigation_manager)

    def _run(
        self,
        filename: str,
        content: str,
        investigation_id: str = ""
    ) -> str:
        """Запись содержимого в файл."""
        # Проверка обязательного наличия investigation_id
        if not investigation_id or investigation_id == "service_request":
            return (
                "Ошибка: investigation_id не указан. "
                "Необходимо сначала создать расследование через create_investigation, "
                "после чего investigation_id будет автоматически добавляться ко всем файловым операциям."
            )

        try:
            asyncio.run(self.investigation_manager.write_file(
                investigation_id=investigation_id,
                filename=filename,
                content=content
            ))
            # return f"Записан файл {filename}"
            return ""
        except (FileNotFoundError, ValueError) as e:
            return f"Ошибка: {str(e)}"


class AppendToFileInput(BaseModel):
    """Схема входных данных для AppendToFileTool."""

    investigation_id: Optional[str] = Field(
        default="",
        description="ID расследования (автоматически добавляется бэкендом, не указывать)"
    )
    filename: str = Field(
        ...,
        description="Имя файла для добавления содержимого"
    )
    content: str = Field(
        ...,
        description="Содержимое для добавления в конец файла"
    )


class AppendToFileTool(BaseTool):
    """
    Инструмент для добавления содержимого в конец существующего файла.

    Используй этот инструмент чтобы:
    - Добавлять новые записи в файлы логов
    - Добавлять дополнительные лабораторные результаты
    - Добавлять последующие наблюдения к существующим файлам

    **Когда использовать:**
    - Файл существует и ты хочешь ДОБАВИТЬ содержимое (не заменить)
    - Добавление последовательных данных (например, ежедневные наблюдения)
    - Добавление новых находок к существующему анализу

    **Когда НЕ использовать:**
    - Когда нужно обновить конкретную секцию (используй update_file_section)
    - Когда создаешь новый файл (используй write_file)
    - Когда полностью заменяешь содержимое (используй write_file)
    """

    name: str = "append_to_file"
    description: str = (
        "Добавляет содержимое в конец существующего файла в расследовании. "
        "Используй чтобы добавить новую информацию без перезаписи существующего содержимого."
    )
    args_schema: Type[BaseModel] = AppendToFileInput

    investigation_manager: InvestigationManager

    def __init__(self, investigation_manager: InvestigationManager):
        super().__init__(investigation_manager=investigation_manager)

    def _run(
        self,
        filename: str,
        content: str,
        investigation_id: str = ""
    ) -> str:
        """Добавление содержимого в конец файла."""
        # Проверка обязательного наличия investigation_id
        if not investigation_id or investigation_id == "service_request":
            return (
                "Ошибка: investigation_id не указан. "
                "Необходимо сначала создать расследование через create_investigation, "
                "после чего investigation_id будет автоматически добавляться ко всем файловым операциям."
            )

        try:
            asyncio.run(self.investigation_manager.append_to_file(
                investigation_id=investigation_id,
                filename=filename,
                content=content
            ))
            return f"Добавлено в файл {filename}"
        except (FileNotFoundError, ValueError) as e:
            return f"Ошибка: {str(e)}"


class UpdateFileSectionInput(BaseModel):
    """Схема входных данных для UpdateFileSectionTool."""

    investigation_id: Optional[str] = Field(
        default="",
        description="ID расследования (автоматически добавляется бэкендом, не указывать)"
    )
    filename: str = Field(
        ...,
        description="Имя Markdown файла для обновления"
    )
    section: str = Field(
        ...,
        description=(
            "Заголовок секции для обновления (например, '## Hypotheses', '# Clinical Findings'). "
            "Должно точно совпадать с заголовком Markdown."
        )
    )
    new_content: str = Field(
        ...,
        description="Новое содержимое для замены секции (без самого заголовка)"
    )


class UpdateFileSectionTool(BaseTool):
    """
    Инструмент для обновления конкретной секции Markdown в файле.

    Используй этот инструмент чтобы:
    - Обновлять ранжирование гипотез по мере поступления новых данных
    - Изменять конкретные секции без переписывания всего файла
    - Обновлять выводы после дополнительного анализа

    **Как это работает:**
    - Находит указанный заголовок секции (например, "## Гипотезы")
    - Заменяет содержимое между этим заголовком и следующим заголовком
    - Сохраняет все остальные секции без изменений

    **Формат секции:**
    - Должен включать маркеры '#': "## Гипотезы", "# Результаты"
    - Секция заканчивается на следующем заголовке того же или более высокого уровня
    - Новое содержимое НЕ должно включать сам заголовок секции

    **Лучшие практики:**
    - Читай файл сначала чтобы увидеть точные заголовки секций
    - Используй точное совпадение заголовка (с учетом регистра)
    - Полезен для обновления конкретных частей больших структурированных файлов
    """

    name: str = "update_file_section"
    description: str = (
        "Обновляет конкретную секцию Markdown в файле расследования. "
        "Находит секцию по заголовку и заменяет её содержимое, сохраняя другие секции. "
        "Используй для целевых обновлений структурированных Markdown файлов."
    )
    args_schema: Type[BaseModel] = UpdateFileSectionInput

    investigation_manager: InvestigationManager

    def __init__(self, investigation_manager: InvestigationManager):
        super().__init__(investigation_manager=investigation_manager)

    def _run(
        self,
        filename: str,
        section: str,
        new_content: str,
        investigation_id: str = ""
    ) -> str:
        """Обновление секции файла."""

        logger.info(
            f"UpdateFileSectionTool called: inv={investigation_id}, file={filename}, section={section[:50]}...")

        # Проверка обязательного наличия investigation_id
        if not investigation_id or investigation_id == "service_request":
            return (
                "Ошибка: investigation_id не указан. "
                "Необходимо сначала создать расследование через create_investigation, "
                "после чего investigation_id будет автоматически добавляться ко всем файловым операциям."
            )

        try:
            asyncio.run(self.investigation_manager.update_file_section(
                investigation_id=investigation_id,
                filename=filename,
                section=section,
                new_content=new_content
            ))
            result = f"Обновлена секция '{section}' в файле {filename}"
            logger.info(f"UpdateFileSectionTool SUCCESS: {result}")
            return result
        except (FileNotFoundError, ValueError) as e:
            error_msg = f"Ошибка: {str(e)}"
            logger.error(f"UpdateFileSectionTool ERROR: {error_msg}")
            return error_msg


class GetInstructionInput(BaseModel):
    """Схема входных данных для GetInstructionTool."""

    problem_type: str = Field(
        ...,
        description=(
            "Тип ветеринарной проблемы. Должен быть один из: "
            "'neonatal_diarrhea' (СВИНЬИ: неонатальная диарея), "
            "'respiratory' (СВИНЬИ: респираторные проблемы), "
            "'prrs' (СВИНЬИ: РРСС). "
            "ВНИМАНИЕ: Все доступные инструкции предназначены ТОЛЬКО для свиней. "
            "Для птицы специализированные инструкции пока недоступны."
        )
    )


class GetInstructionTool(BaseTool):
    """
    Инструмент для получения специализированных инструкций/протоколов расследования.

    Используй этот инструмент чтобы получить детальные пошаговые протоколы расследования
    для конкретных типов проблем. Эти инструкции предоставляют систематический подход
    к расследованию различных ветеринарных проблем.

    **ВАЖНО: Все доступные протоколы предназначены ТОЛЬКО для СВИНЕЙ!**
    **Для птицы специализированные инструкции пока недоступны.**

    **Доступные протоколы (ДЛЯ СВИНЕЙ):**
    - neonatal_diarrhea: Протокол расследования диареи у поросят 0-15 дней
    - respiratory: Протокол расследования респираторных проблем (кашель, одышка)
    - prrs: Протокол расследования PRRS (репродуктивные + респираторные признаки)
    - circovirus: Протокол расследования цирковируса свиней (PCV2/PCV3)

    **Когда использовать:**
    - После идентификации типа проблемы в Шаге 1 (общий чеклист)
    - Перед созданием специализированных чеклистов (03_checklist_specific.md)
    - Когда нужна помощь по этапам расследования для конкретной проблемы
    - ТОЛЬКО если текущее расследование касается СВИНЕЙ

    **Что предоставляет:**
    - Систематические этапы расследования
    - Специфические чеклисты сбора данных
    - Распространенные дифференциальные диагнозы
    - Рекомендуемые диагностические тесты
    - Протоколы лечения и профилактики

    Возвращает полный документ инструкции как текст.
    """

    name: str = "get_instruction"
    description: str = (
        "Получает специализированный ветеринарный протокол расследования для конкретного типа проблемы. "
        "ВНИМАНИЕ: Все доступные инструкции предназначены ТОЛЬКО для СВИНЕЙ! "
        "Доступные типы (ДЛЯ СВИНЕЙ): 'neonatal_diarrhea' (неонатальная диарея у поросят), "
        "'respiratory' (респираторные проблемы у свиней), 'prrs' (РРСС у свиней), "
        "'circovirus' (цирковирус свиней PCV2/PCV3). "
        "Для птицы специализированные инструкции пока недоступны. "
        "Используй после идентификации типа проблемы ТОЛЬКО если расследование касается свиней."
    )
    args_schema: Type[BaseModel] = GetInstructionInput

    # Path to instructions directory
    instructions_dir: Path = Path(
        __file__).parent.parent.parent.parent / "agent-workspace" / "instructions"

    def _run(self, problem_type: str) -> str:
        """Получение инструкции для типа проблемы."""
        # Маппинг типов проблем на имена файлов
        instruction_files = {
            "neonatal_diarrhea": "neonatal_diarrhea.md",
            "respiratory": "respiratory.md",
            "prrs": "prrs.md",
            "circovirus": "swine_circovirus_instruction.md",
        }

        if problem_type not in instruction_files:
            available = ", ".join(f"'{k}'" for k in instruction_files.keys())
            return (
                f"Ошибка: Неизвестный тип проблемы '{problem_type}'. "
                f"Доступные типы: {available}"
            )

        instruction_file = self.instructions_dir / \
            instruction_files[problem_type]

        if not instruction_file.exists():
            return (
                f"Ошибка: Файл инструкции не найден: {instruction_file}\n"
                f"Ожидаемое расположение: agent-workspace/instructions/{instruction_files[problem_type]}"
            )

        try:
            content = instruction_file.read_text(encoding="utf-8")
            return (
                f"Загружена инструкция для '{problem_type}':\n\n"
                f"Источник: instructions/{instruction_files[problem_type]}\n"
                f"Длина: {len(content)} символов\n\n"
                f"--- СОДЕРЖИМОЕ ИНСТРУКЦИИ ---\n\n"
                f"{content}"
            )
        except Exception as e:
            return f"Ошибка чтения файла инструкции: {str(e)}"


def create_investigation_tools(
    investigation_manager: InvestigationManager
) -> List[BaseTool]:
    """
    Create all investigation file operation tools.

    Args:
        investigation_manager: Initialized InvestigationManager instance

    Returns:
        List of Langchain BaseTool instances for investigation operations
    """
    return [
        # CreateInvestigationTool убран - расследования создаются автоматически по conversation
        # ListInvestigationsTool убран - меньше путаницы, каждая сессия = одно расследование
        ListFilesTool(investigation_manager=investigation_manager),
        ReadFileTool(investigation_manager=investigation_manager),
        WriteFileTool(investigation_manager=investigation_manager),
        AppendToFileTool(investigation_manager=investigation_manager),
        UpdateFileSectionTool(investigation_manager=investigation_manager),
        GetInstructionTool(),  # Не требует investigation_manager
    ]
