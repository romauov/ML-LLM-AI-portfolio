"""
Парсер markdown инструкций препаратов.

Парсит markdown файлы инструкций и извлекает:
- Метаданные препарата (название, действующее вещество, производитель и т.д.)
- Секции инструкции (показания, дозирование, противопоказания и т.д.)
"""

import re
import ast
import csv
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from app.utils.logger import get_logger


logger = get_logger(__name__)


# Маппинг заголовков секций на типы
# ВАЖНО: Порядок имеет значение! Более специфичные паттерны должны быть первыми
SECTION_TYPE_MAPPING = {
    # Сначала проверяем противопоказания (перед "показания")
    'противопоказания': 'contraindications',
    # Потом показания
    'показания к применению': 'indications',
    # Состав
    'состав и форма выпуска': 'composition',
    'состав': 'composition',
    'форма выпуска': 'composition',
    # Фармакологические свойства
    'фармакологические свойства': 'properties',
    'фармакологическое действие': 'properties',
    'биологические свойства': 'properties',
    'механизм действия': 'properties',
    # Дозирование
    'режим дозирования': 'dosing',
    'дозирование': 'dosing',
    'способ применения и дозы': 'dosing',
    'дозы и способ применения': 'dosing',
    'дозировка': 'dosing',
    # Особые указания
    'особые указания': 'special_notes',
    'меры предосторожности': 'special_notes',
    'предостережения': 'special_notes',
    # Хранение
    'условия и сроки хранения': 'storage',
    'условия хранения': 'storage',
    'срок годности': 'storage',
    'хранение': 'storage',
    # Преимущества
    'преимущества': 'advantages',
    # Побочные эффекты
    'побочные действия': 'side_effects',
    'побочные эффекты': 'side_effects',
    'нежелательные реакции': 'side_effects',
    # Взаимодействия
    'взаимодействие с другими препаратами': 'interactions',
    'лекарственное взаимодействие': 'interactions',
    # Передозировка
    'передозировка': 'overdose',
}


@dataclass
class DrugMetadata:
    """Метаданные препарата из заголовка инструкции."""
    trade_name: str
    generic_name: Optional[str] = None
    drug_class: Optional[str] = None
    dosage_form: Optional[str] = None
    route: Optional[str] = None
    target_animals: list[str] = field(default_factory=list)
    manufacturer: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class InstructionSection:
    """Секция инструкции препарата."""
    title: str  # Оригинальный заголовок
    section_type: str  # Нормализованный тип секции
    content: str  # Содержимое секции
    level: int  # Уровень заголовка (2 для ##, 3 для ###)


@dataclass
class ParsedInstruction:
    """Результат парсинга инструкции."""
    metadata: DrugMetadata
    sections: list[InstructionSection]
    source_file: str
    raw_content: str


class DrugInstructionParser:
    """Парсер markdown инструкций препаратов."""

    # Регулярные выражения для парсинга метаданных
    METADATA_PATTERNS = {
        'generic_name': re.compile(r'\*\*Действующее вещество\*\*:\s*(.+)'),
        'drug_class': re.compile(r'\*\*Фармакологическая группа\*\*:\s*(.+)'),
        'dosage_form': re.compile(r'\*\*Лекарственная форма\*\*:\s*(.+)'),
        'route': re.compile(r'\*\*Способ применения\*\*:\s*(.+)'),
        'manufacturer': re.compile(r'\*\*Производитель препарата\*\*:\s*(.+)'),
        'target_animals': re.compile(r'\*\*Список животных\*\*:\s*(.+)'),
        'source_url': re.compile(r'\*\*Исходная инструкция\*\*:\s*\[.+\]\((.+)\)'),
    }

    # Регулярное выражение для заголовков
    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    def __init__(self, instructions_dir: str | Path = 'instructions'):
        """
        Инициализация парсера.

        Args:
            instructions_dir: Путь к директории с инструкциями
        """
        self.instructions_dir = Path(instructions_dir)

    def parse_instructions(self) -> list[ParsedInstruction]:
        """
        Парсинг всех файлов инструкций в директории.

        Returns:
            Список ParsedInstruction для всех файлов
        """
        md_files = sorted(self.instructions_dir.glob('*.md'))

        if not md_files:
            logger.warning(f'В директории {self.instructions_dir} не найдено .md файлов')
            return []

        logger.info(f'Найдено {len(md_files)} файлов инструкций')

        results = []
        for file_path in md_files:
            try:
                parsed = self._parse_single_file(file_path)
                results.append(parsed)
            except Exception as e:
                logger.error(f'Ошибка парсинга {file_path.name}: {e}')

        logger.info(f'Успешно распаршено {len(results)} инструкций')
        return results

    def _parse_single_file(self, file_path: Path) -> ParsedInstruction:
        """
        Парсинг одного файла инструкции.

        Args:
            file_path: Путь к файлу markdown

        Returns:
            ParsedInstruction с метаданными и секциями
        """
        logger.info(f'Парсинг файла: {file_path.name}')

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        metadata = self._parse_metadata(content, file_path.name)
        sections = self._parse_sections(content)

        return ParsedInstruction(
            metadata=metadata,
            sections=sections,
            source_file=file_path.name,
            raw_content=content
        )

    def _parse_metadata(self, content: str, filename: str) -> DrugMetadata:
        """
        Извлечение метаданных из содержимого инструкции.

        Args:
            content: Содержимое markdown файла
            filename: Имя файла для извлечения trade_name

        Returns:
            DrugMetadata с извлечёнными данными
        """
        # Извлечение trade_name из первого заголовка (# Название)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        trade_name = title_match.group(1).strip() if title_match else filename.replace('.md', '')

        # Очистка trade_name от символов типа ® и ™
        trade_name = re.sub(r'[®™©]', '', trade_name).strip()

        metadata_dict = {'trade_name': trade_name}

        # Извлечение остальных полей по паттернам
        for field_name, pattern in self.METADATA_PATTERNS.items():
            match = pattern.search(content)
            if match:
                value = match.group(1).strip()

                # Специальная обработка для списка животных
                if field_name == 'target_animals':
                    try:
                        # Парсим как Python list
                        animals = ast.literal_eval(value)
                        if isinstance(animals, list):
                            metadata_dict[field_name] = animals
                        else:
                            metadata_dict[field_name] = [value]
                    except (ValueError, SyntaxError):
                        # Если не удалось распарсить, пробуем разделить по запятым
                        metadata_dict[field_name] = [a.strip() for a in value.split(',')]
                else:
                    metadata_dict[field_name] = value

        return DrugMetadata(**metadata_dict)

    def _parse_sections(self, content: str) -> list[InstructionSection]:
        """
        Извлечение секций из содержимого инструкции.

        Args:
            content: Содержимое markdown файла

        Returns:
            Список InstructionSection
        """
        sections = []
        headers = list(self.HEADER_PATTERN.finditer(content))

        for i, header_match in enumerate(headers):
            level = len(header_match.group(1))
            title = header_match.group(2).strip()

            # Пропускаем заголовок первого уровня (название препарата)
            if level == 1:
                continue

            # Пропускаем заголовок "Инструкция" (## Инструкция)
            if title.lower() == 'инструкция':
                continue

            # Определяем начало и конец контента секции
            content_start = header_match.end()
            content_end = headers[i + 1].start() if i + 1 < len(headers) else len(content)
            section_content = content[content_start:content_end].strip()

            # Определяем тип секции через маппинг
            title_lower = title.lower().strip()
            section_type = 'other'

            # Ищем совпадение по паттернам из маппинга
            for pattern, mapped_type in SECTION_TYPE_MAPPING.items():
                if pattern in title_lower:
                    section_type = mapped_type
                    break

            if section_type == 'other':
                logger.debug(f'Неизвестный тип секции: {title}')

            sections.append(InstructionSection(
                title=title,
                section_type=section_type,
                content=section_content,
                level=level
            ))

        return sections

    def to_table_rows(self, instructions: list[ParsedInstruction]) -> list[dict]:
        """
        Преобразование списка инструкций в строки таблицы.

        Args:
            instructions: Список распаршенных инструкций

        Returns:
            Список словарей с данными для CSV
        """
        return [self._instruction_to_row(parsed) for parsed in instructions]

    def _instruction_to_row(self, parsed: ParsedInstruction) -> dict:
        """
        Преобразование одной инструкции в строку таблицы.

        Args:
            parsed: Распаршенная инструкция

        Returns:
            Словарь с данными для CSV
        """
        metadata = parsed.metadata

        # Извлекаем все содержимое секций с правильным уровнем заголовков
        full_content = '\n\n'.join(
            f"{'#' * section.level} {section.title}\n{section.content}"
            for section in parsed.sections
        )

        return {
            'trade_name': metadata.trade_name,
            'generic_name': metadata.generic_name or '',
            'drug_class': metadata.drug_class or '',
            'dosage_form': metadata.dosage_form or '',
            'route': metadata.route or '',
            'target_animals': ', '.join(metadata.target_animals) if metadata.target_animals else '',
            'manufacturer': metadata.manufacturer or '',
            'source_url': metadata.source_url or '',
            'source_file': parsed.source_file,
            'content': full_content
        }

    def export_to_csv(self, output_file: str | Path = 'instructions_table.csv') -> Path:
        """
        Парсинг инструкций и экспорт в CSV файл.

        Args:
            output_file: Путь к выходному CSV файлу

        Returns:
            Path к созданному файлу
        """
        output_path = Path(output_file)

        # Парсим все инструкции
        instructions = self.parse_instructions()

        if not instructions:
            logger.warning('Нет инструкций для экспорта')
            return output_path

        # Преобразуем в строки таблицы
        table_rows = self.to_table_rows(instructions)

        # Записываем в CSV
        fieldnames = [
            'trade_name',
            'generic_name',
            'drug_class',
            'dosage_form',
            'route',
            'target_animals',
            'manufacturer',
            'source_url',
            'source_file',
            'content'
        ]

        with open(output_path, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(table_rows)

        logger.info(
            f'Экспортировано {len(table_rows)} инструкций в {output_path.absolute()}'
        )
        return output_path
