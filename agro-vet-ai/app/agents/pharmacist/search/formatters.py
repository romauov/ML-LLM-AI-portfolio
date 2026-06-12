"""
Форматирование результатов поиска в различные форматы.

Содержит:
- MarkdownFormatter: Рендеринг инструкций препаратов в Markdown
- Потенциально другие форматы в будущем (JSON, XML, HTML)
"""

from typing import Optional
from app.utils.logger import get_logger


class MarkdownFormatter:
    """Форматирование данных препаратов в Markdown."""

    # Порядок секций для красивого вывода
    SECTION_ORDER = [
        'composition', 'properties', 'indications', 'dosing',
        'contraindications', 'side_effects', 'interactions',
        'overdose', 'special_notes', 'storage', 'advantages'
    ]

    def __init__(self):
        self.logger = get_logger(__name__)

    def format_drug_instruction(
        self,
        trade_name: str,
        chunks: list[dict]
    ) -> Optional[str]:
        """
        Форматирование полной инструкции препарата в Markdown.

        Собирает все чанки препарата и форматирует их в единый MD файл
        с заголовками и структурой.

        Args:
            trade_name: Торговое название препарата
            chunks: Список словарей с данными чанков
                Ожидаемые поля: content, section_type, section_title

        Returns:
            Markdown-форматированная инструкция или None
        """
        if not chunks:
            self.logger.warning(f'[Formatter] Нет чанков для препарата "{trade_name}"')
            return None

        try:
            # Формируем заголовок документа
            md_parts = [f"# {trade_name}\n"]
            md_parts.append("\n---\n")

            # Собираем секции
            sections = {}
            for chunk in chunks:
                section_type = chunk.get('section_type') or "other"
                if section_type not in sections:
                    sections[section_type] = {
                        'title': chunk.get('section_title') or section_type,
                        'content': []
                    }
                sections[section_type]['content'].append(chunk.get('content', ''))

            # Добавляем секции в порядке
            # Чанки уже содержат заголовки (### Title) и разделители (---), просто выводим их
            for section_type in self.SECTION_ORDER:
                if section_type in sections:
                    section_data = sections[section_type]
                    md_parts.append('\n\n'.join(section_data['content']))
                    md_parts.append("\n\n")

            # Добавляем оставшиеся секции, которых нет в порядке
            for section_type, section_data in sections.items():
                if section_type not in self.SECTION_ORDER:
                    md_parts.append('\n\n'.join(section_data['content']))
                    md_parts.append("\n\n")

            return ''.join(md_parts)

        except Exception as e:
            self.logger.error(f'[Formatter] Ошибка создания MD инструкции: {e}')
            return None

    def format_drug_metadata(self, metadata: dict) -> str:
        """
        Форматирование метаданных препарата в читаемый вид.

        Args:
            metadata: Словарь с метаданными препарата
                Ожидаемые поля: trade_name, generic_name, drug_class,
                dosage_form, route, manufacturer, target_animals

        Returns:
            Отформатированная строка с метаданными
        """
        parts = []

        if metadata.get('trade_name'):
            parts.append(f"**Торговое название:** {metadata['trade_name']}")

        if metadata.get('generic_name'):
            parts.append(f"**Действующее вещество:** {metadata['generic_name']}")

        if metadata.get('drug_class'):
            parts.append(f"**Класс:** {metadata['drug_class']}")

        if metadata.get('dosage_form'):
            parts.append(f"**Форма выпуска:** {metadata['dosage_form']}")

        if metadata.get('route'):
            parts.append(f"**Способ применения:** {metadata['route']}")

        if metadata.get('manufacturer'):
            parts.append(f"**Производитель:** {metadata['manufacturer']}")

        if metadata.get('target_animals'):
            animals = metadata['target_animals']
            if isinstance(animals, list):
                animals_str = ', '.join(animals)
            else:
                animals_str = str(animals)
            parts.append(f"**Целевые животные:** {animals_str}")

        return '\n'.join(parts) if parts else "Метаданные отсутствуют"

    def format_search_results(
        self,
        chunks: list[dict],
        include_distance: bool = True,
        max_content_length: int = 300
    ) -> str:
        """
        Форматирование результатов поиска в читаемый вид.

        Args:
            chunks: Список словарей с данными чанков
            include_distance: Включать ли косинусное расстояние
            max_content_length: Максимальная длина контента для отображения

        Returns:
            Отформатированная строка с результатами
        """
        if not chunks:
            return "Результаты не найдены"

        parts = []
        for i, chunk in enumerate(chunks, 1):
            trade_name = chunk.get('trade_name', 'Unknown')
            section_title = chunk.get('section_title', '')
            content = chunk.get('content', '')

            # Обрезаем контент если слишком длинный
            if len(content) > max_content_length:
                content = content[:max_content_length] + '...'

            result = f"**{i}. {trade_name}**"
            if section_title:
                result += f" - {section_title}"

            if include_distance and chunk.get('distance') is not None:
                result += f" (distance: {chunk['distance']:.3f})"

            result += f"\n{content}\n"
            parts.append(result)

        return '\n---\n'.join(parts)
