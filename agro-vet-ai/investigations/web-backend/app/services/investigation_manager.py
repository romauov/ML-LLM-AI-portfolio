"""Investigation Manager for file operations."""
import aiofiles
import aiofiles.os as aios
import asyncio
from pathlib import Path
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.models.investigation import (
    Investigation,
    InvestigationCreate,
    InvestigationFile,
    InvestigationListItem,
    InvestigationStatus,
)


class InvestigationManager:
    """Manages investigation files and directories."""

    def __init__(self, workspace_path: str):
        """
        Initialize Investigation Manager.

        Args:
            workspace_path: Path to investigations directory (already includes 'investigations' folder)
        """
        self.workspace_path = Path(workspace_path).resolve(
        ).parent  # Parent is agent-workspace
        # This IS investigations directory
        self.investigations_path = Path(workspace_path).resolve()

        # Ensure investigations directory exists
        self.investigations_path.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, path: Path) -> None:
        """
        Validate that path is within investigations directory.

        Args:
            path: Path to validate

        Raises:
            ValueError: If path is outside investigations directory
        """
        try:
            path.resolve().relative_to(self.investigations_path.resolve())
        except ValueError:
            raise ValueError(f"Path {path} is outside investigations directory")

    def _sanitize_farm_name(self, farm_name: str) -> str:
        """
        Sanitize farm name for use in directory name.

        Args:
            farm_name: Farm name to sanitize

        Returns:
            Sanitized farm name
        """
        # Remove special characters, keep only alphanumeric, dash, underscore
        sanitized = re.sub(r'[^\w\-]', '_', farm_name.lower())
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        return sanitized.strip('_')

    async def create_investigation_folder(self, investigation_id: str) -> Path:
        """
        Создать папку расследования с минимальной структурой.

        Используется для автоматически создаваемых расследований (по conversation).
        Создаёт только папку и базовый файл STATUS.md.

        Args:
            investigation_id: ID расследования (формат: YYYYMMDD_HHMMSS_random6)

        Returns:
            Path к созданной папке расследования

        Raises:
            ValueError: Если расследование уже существует или путь невалидный
        """
        inv_path = self.investigations_path / investigation_id

        # Асинхронная проверка существования
        if await aios.path.exists(inv_path):
            # Расследование уже существует, возвращаем путь
            return inv_path

        # Проверка пути (можно оставить синхронной, т.к. не делает I/O)
        self._validate_path(inv_path)

        # Асинхронное создание директории
        await aios.makedirs(inv_path, exist_ok=True)

        # Создаём минимальный STATUS.md
        status_content = f"""# Статус расследования

**Investigation ID:** {investigation_id}
**Статус:** Активно
**Создано:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Прогресс

- [x] Расследование инициировано
- [ ] Собраны начальные данные
- [ ] Сформулированы гипотезы
- [ ] Сформулированы выводы
- [ ] Создан финальный отчёт

## Примечания

Расследование автоматически создано из чата.
"""
        # Используем асинхронную запись файла
        await self.write_file(investigation_id, "STATUS.md", status_content)

        return inv_path

    async def create_investigation(
        self,
        farm_name: str,
        animal_type: str,
        problem_type: str,
        description: str
    ) -> Investigation:
        """
        Create a new investigation with directory and initial files.

        Args:
            farm_name: Name of the farm
            animal_type: Type of animals
            problem_type: Type of problem
            description: Initial description

        Returns:
            Created investigation object

        Raises:
            ValueError: If investigation already exists or path is invalid
        """
        # Generate investigation ID
        date_str = datetime.now().strftime("%Y%m%d")
        sanitized_name = self._sanitize_farm_name(farm_name)
        investigation_id = f"{date_str}_{sanitized_name}_{problem_type.lower()}"

        # Create investigation directory
        inv_path = self.investigations_path / investigation_id

        # Асинхронная проверка существования
        if await aios.path.exists(inv_path):
            raise ValueError(
                f"Investigation {investigation_id} already exists")

        self._validate_path(inv_path)
        await aios.makedirs(inv_path, exist_ok=True)

        # Create STATUS.md
        status_content = f"""# Investigation Status

**Investigation ID:** {investigation_id}
**Farm:** {farm_name}
**Animal Type:** {animal_type}
**Problem Type:** {problem_type}
**Status:** Active
**Created:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Progress

- [x] Investigation initiated
- [ ] Initial data collected
- [ ] Hypotheses formed
- [ ] Additional data requested
- [ ] Conclusions drawn
- [ ] Report finalized

## Notes

{description}
"""
        await self.write_file(investigation_id, "STATUS.md", status_content)

        # Create 00_incident.md
        incident_content = f"""# Incident Description

**Farm:** {farm_name}
**Animal Type:** {animal_type}
**Problem Type:** {problem_type}
**Date:** {datetime.now().strftime("%Y-%m-%d")}

## Initial Description

{description}

## Additional Information

_To be filled in during investigation_
"""
        await self.write_file(investigation_id, "00_incident.md", incident_content)

        # Create 01_group_card.md (template)
        group_card_content = """# Group Card

## Basic Information

- **Group ID:**
- **Number of Animals:**
- **Age:**
- **Weight:**

## Housing

- **Building/Pen:**
- **Ventilation:**
- **Temperature:**
- **Humidity:**

## Feeding

- **Feed Type:**
- **Feeding Regime:**
- **Water Access:**

## History

- **Vaccination:**
- **Previous Treatments:**
- **Recent Changes:**

_To be filled in during investigation_
"""
        await self.write_file(investigation_id, "01_group_card.md",
                              group_card_content)

        # Return investigation object
        return Investigation(
            id=investigation_id,
            farm_name=farm_name,
            animal_type=animal_type,
            problem_type=problem_type,
            status=InvestigationStatus.ACTIVE,
            created_at=datetime.now(),
            path=str(inv_path),
        )

    async def list_investigations(self) -> List[InvestigationListItem]:
        """
        List all investigations.

        Returns:
            List of investigation items
        """
        investigations = []

        # Асинхронно получаем список директорий
        try:
            # Используем asyncio.to_thread для получения списка директорий
            items = await asyncio.to_thread(
                lambda: list(self.investigations_path.iterdir())
            )
        except Exception as e:
            print(f"Error reading investigations directory: {e}")
            return []

        # Создаем задачи для обработки каждой директории
        tasks = [self._process_investigation_dir(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Фильтруем успешные результаты
        for result in results:
            if isinstance(result, InvestigationListItem):
                investigations.append(result)
            elif isinstance(result, Exception):
                # Логируем ошибки, но не прерываем выполнение
                print(f"Error processing investigation: {result}")

        # Sort by creation date (newest first)
        investigations.sort(key=lambda x: x.created_at, reverse=True)
        return investigations

    async def _process_investigation_dir(self, item_path: Path) -> Optional[InvestigationListItem]:
        """
        Process a single investigation directory.

        Args:
            item_path: Path to investigation directory

        Returns:
            InvestigationListItem or None if not valid
        """
        # Проверяем, что это директория и не скрытая
        try:
            is_dir = await aios.path.isdir(item_path)
            if not is_dir or item_path.name.startswith('.'):
                return None
        except Exception:
            return None

        try:
            # Получаем информацию о директории
            stat_info = await aios.stat(item_path)
            created_at = datetime.fromtimestamp(stat_info.st_ctime)

            # Пытаемся прочитать статус
            status = InvestigationStatus.ACTIVE
            farm_name = item_path.name

            # Пробуем прочитать STATUS.md асинхронно
            try:
                status_content = await self.read_file(item_path.name, "STATUS.md")

                # Parse status from STATUS.md
                if "Status:** Completed" in status_content or "Status:** completed" in status_content:
                    status = InvestigationStatus.COMPLETED
                elif "Status:** Pending" in status_content or "Status:** pending" in status_content:
                    status = InvestigationStatus.PENDING
                elif "Status:** Archived" in status_content or "Status:** archived" in status_content:
                    status = InvestigationStatus.ARCHIVED

                # Try to extract farm name
                match = re.search(r'\*\*Farm:\*\*\s*(.+)', status_content)
                if match:
                    farm_name = match.group(1).strip()
                else:
                    # Try alternative patterns
                    patterns = [
                        r'Farm:\s*(.+)',
                        r'Ферма:\s*(.+)',
                        r'Farm Name:\s*(.+)',
                        r'\*\*Farm\*\*:\s*(.+)'
                    ]
                    for pattern in patterns:
                        match = re.search(
                            pattern, status_content, re.IGNORECASE)
                        if match:
                            farm_name = match.group(1).strip()
                            break

            except Exception as e:
                # Если не удалось прочитать STATUS.md, используем значения по умолчанию
                print(f"Could not read STATUS.md for {item_path.name}: {e}")
                pass

            return InvestigationListItem(
                id=item_path.name,
                farm_name=farm_name,
                status=status,
                created_at=created_at,
                path=str(item_path)
            )

        except Exception as e:
            print(f"Error processing investigation {item_path.name}: {e}")
            return None

    async def get_investigation(self, investigation_id: str) -> Investigation:
        """
        Get investigation details.

        Args:
            investigation_id: Investigation ID

        Returns:
            Investigation object

        Raises:
            FileNotFoundError: If investigation doesn't exist
            ValueError: If investigation is invalid
        """
        inv_path = self.investigations_path / investigation_id

        # Асинхронная проверка существования
        if not await aios.path.exists(inv_path):
            raise FileNotFoundError(
                f"Investigation {investigation_id} not found")

        self._validate_path(inv_path)

        # Получаем информацию о директории
        stat_info = await aios.stat(inv_path)
        created_at = datetime.fromtimestamp(stat_info.st_ctime)

        # Читаем STATUS.md
        try:
            status_content = await self.read_file(investigation_id, "STATUS.md")

            # Парсим детали
            farm_name = investigation_id
            animal_type = "unknown"
            problem_type = "unknown"
            status = InvestigationStatus.ACTIVE

            match = re.search(r'\*\*Farm:\*\*\s*(.+)', status_content)
            if match:
                farm_name = match.group(1).strip()

            match = re.search(r'\*\*Animal Type:\*\*\s*(.+)', status_content)
            if match:
                animal_type = match.group(1).strip()

            match = re.search(r'\*\*Problem Type:\*\*\s*(.+)', status_content)
            if match:
                problem_type = match.group(1).strip()

            if "Status:** Completed" in status_content:
                status = InvestigationStatus.COMPLETED
            elif "Status:** Pending" in status_content:
                status = InvestigationStatus.PENDING

        except Exception:
            # Если не удалось прочитать статус, используем значения по умолчанию
            farm_name = investigation_id
            animal_type = "unknown"
            problem_type = "unknown"
            status = InvestigationStatus.ACTIVE

        return Investigation(
            id=investigation_id,
            farm_name=farm_name,
            animal_type=animal_type,
            problem_type=problem_type,
            status=status,
            created_at=created_at,
            path=str(inv_path),
        )

    async def list_files(self, investigation_id: str) -> List[str]:
        """
        List all files in investigation.

        Args:
            investigation_id: Investigation ID

        Returns:
            List of filenames

        Raises:
            FileNotFoundError: If investigation doesn't exist
        """
        inv_path = self.investigations_path / investigation_id

        # Асинхронная проверка существования
        if not await aios.path.exists(inv_path):
            raise FileNotFoundError(
                f"Investigation {investigation_id} not found")

        self._validate_path(inv_path)

        # Получаем список файлов асинхронно
        try:
            # Используем asyncio.to_thread для получения списка файлов
            def list_files_sync(path: Path) -> List[str]:
                return [item.name for item in path.iterdir() if item.is_file()]

            files = await asyncio.to_thread(list_files_sync, inv_path)
            return sorted(files)

        except Exception as e:
            raise RuntimeError(
                f"Error listing files in investigation {investigation_id}: {e}")

    async def read_file(self, investigation_id: str, filename: str) -> str:
        """
        Read file from investigation.

        Args:
            investigation_id: Investigation ID
            filename: Name of the file to read

        Returns:
            File content

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If path is invalid
        """
        file_path = self.investigations_path / investigation_id / filename

        # Асинхронная проверка существования
        if not await aios.path.exists(file_path):
            raise FileNotFoundError(
                f"File {filename} not found in {investigation_id}")

        self._validate_path(file_path)

        # Асинхронное чтение файла
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return content
        except UnicodeDecodeError:
            # Если не удалось прочитать как utf-8, пробуем другие кодировки
            try:
                async with aiofiles.open(file_path, 'r', encoding='cp1251') as f:
                    content = await f.read()
                return content
            except Exception as e:
                raise IOError(f"Cannot read file {filename}: {e}")
        except Exception as e:
            raise IOError(f"Cannot read file {filename}: {e}")

    async def write_file(self, investigation_id: str, filename: str, content: str) -> None:
        """
        Write file to investigation (create or overwrite).

        Args:
            investigation_id: Investigation ID
            filename: Name of the file
            content: Content to write

        Raises:
            FileNotFoundError: If investigation doesn't exist
            ValueError: If path is invalid
        """
        inv_path = self.investigations_path / investigation_id

        # Асинхронная проверка существования директории
        if not await aios.path.exists(inv_path):
            raise FileNotFoundError(
                f"Investigation {investigation_id} not found")

        file_path = inv_path / filename
        # Если этот метод не I/O, можно оставить синхронным
        self._validate_path(file_path)

        # Асинхронная запись файла
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(content)

    async def append_to_file(self, investigation_id: str, filename: str, content: str) -> None:
        """
        Append content to file.

        Args:
            investigation_id: Investigation ID
            filename: Name of the file
            content: Content to append

        Raises:
            FileNotFoundError: If investigation doesn't exist
            ValueError: If path is invalid
        """
        inv_path = self.investigations_path / investigation_id

        # Асинхронная проверка существования директории
        if not await aios.path.exists(inv_path):
            raise FileNotFoundError(
                f"Investigation {investigation_id} not found")

        file_path = inv_path / filename
        # Если этот метод не I/O, можно оставить синхронным
        self._validate_path(file_path)

        # Асинхронное добавление в файл
        async with aiofiles.open(file_path, 'a', encoding='utf-8') as f:
            await f.write(content)

    async def update_file_section(
        self,
        investigation_id: str,
        filename: str,
        section: str,
        new_content: str
    ) -> None:
        """
        Update a specific section in a markdown file.

        Args:
            investigation_id: Investigation ID
            filename: Name of the file
            section: Section header (e.g., "## Hypotheses")
            new_content: New content for the section

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If path is invalid or section not found
        """
        current_content = await self.read_file(investigation_id, filename)

        # Find section boundaries
        section_pattern = re.compile(
            rf'^(#{1,6}\s+{re.escape(section.lstrip("#").strip())})\s*$',
            re.MULTILINE | re.IGNORECASE
        )

        match = section_pattern.search(current_content)
        if not match:
            raise ValueError(f"Section '{section}' not found in {filename}")

        section_start = match.end()

        # Find next section (same or higher level heading)
        section_level = len(match.group(1).split()[0])  # Count '#' characters
        next_section_pattern = re.compile(
            rf'^#{{{1,{section_level}}}}\s+',
            re.MULTILINE
        )

        next_match = next_section_pattern.search(
            current_content, section_start)
        section_end = next_match.start() if next_match else len(current_content)

        # Replace section content
        new_file_content = (
            current_content[:section_start] +
            '\n' + new_content.strip() + '\n\n' +
            current_content[section_end:]
        )

        await self.write_file(investigation_id, filename, new_file_content)
