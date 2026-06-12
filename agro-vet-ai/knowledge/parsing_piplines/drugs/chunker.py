"""
Chunker для инструкций препаратов.

Нарезает инструкции на чанки для RAG и подготавливает их
для вставки в таблицу drugs_chunks.
"""

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from knowledge.parsing_piplines.drugs.instruction_parser import (
    DrugInstructionParser,
    ParsedInstruction,
)
from app.utils.logger import get_logger


logger = get_logger(__name__)


@dataclass
class DrugChunkData:
    """Данные чанка для вставки в БД."""
    content: str
    section_type: str
    section_title: str
    trade_name: str
    generic_name: str | None
    drug_class: str | None
    dosage_form: str | None
    route: str | None
    target_animals: list[str] | None
    source_file: str
    manufacturer: str | None
    source_url: str | None


@dataclass
class DrugChunksResult:
    """Результат нарезки инструкции на чанки."""
    trade_name: str
    generic_name: str | None
    target_animals: list[str]
    chunks: list[DrugChunkData] = field(default_factory=list)


class DrugChunker:
    """
    Chunker для нарезки инструкций препаратов.

    Стратегия нарезки:
    - Каждая секция инструкции (### заголовок) становится отдельным чанком
    - Если секция слишком длинная (>2000 символов), она разбивается на части
    - Каждый чанк включает контекст: название препарата + заголовок секции
    """

    # Максимальный размер чанка в символах
    MAX_CHUNK_SIZE = 2000

    # Минимальный размер чанка (0 = все секции включаются)
    MIN_CHUNK_SIZE = 0

    def __init__(self, instructions_dir: str | Path = 'instructions'):
        """
        Инициализация chunker.

        Args:
            instructions_dir: Путь к директории с инструкциями
        """
        self.parser = DrugInstructionParser(instructions_dir)

    def process_file(self, file_path: str | Path) -> DrugChunksResult:
        """
        Обработка одного файла инструкции.

        Args:
            file_path: Путь к файлу markdown

        Returns:
            DrugChunksResult с чанками
        """
        parsed = self.parser._parse_single_file(Path(file_path))
        return self._create_chunks(parsed)

    def process_all(self) -> list[DrugChunksResult]:
        """
        Обработка всех файлов инструкций.

        Returns:
            Список DrugChunksResult для каждого файла
        """
        results = []
        parsed_instructions = self.parser.parse_instructions()

        for parsed in parsed_instructions:
            try:
                chunks_result = self._create_chunks(parsed)
                results.append(chunks_result)
                logger.debug(
                    f'{parsed.metadata.trade_name}: '
                    f'создано {len(chunks_result.chunks)} чанков'
                )
            except Exception as e:
                logger.error(
                    f'Ошибка создания чанков для {parsed.source_file}: {e}'
                )

        total_chunks = sum(len(r.chunks) for r in results)
        logger.info(
            f'Обработано {len(results)} инструкций, '
            f'создано {total_chunks} чанков'
        )
        return results

    def _create_chunks(self, parsed: ParsedInstruction) -> DrugChunksResult:
        """
        Создание чанков из распаршенной инструкции.

        Args:
            parsed: Распаршенная инструкция

        Returns:
            DrugChunksResult с чанками
        """
        metadata = parsed.metadata
        chunks: list[DrugChunkData] = []

        for section in parsed.sections:
            # Формируем полный контент чанка с markdown-заголовком (важен для embeddings)
            # Используем --- как разделитель между заголовком и контентом
            chunk_content = f"### {section.title}\n\n---\n\n{section.content}"

            # Если секция короткая, создаём один чанк
            if len(section.content) <= self.MAX_CHUNK_SIZE:
                if len(section.content) >= self.MIN_CHUNK_SIZE:
                    chunks.append(DrugChunkData(
                        content=chunk_content,
                        section_type=section.section_type,
                        section_title=section.title,
                        trade_name=metadata.trade_name,
                        generic_name=metadata.generic_name,
                        drug_class=metadata.drug_class,
                        dosage_form=metadata.dosage_form,
                        route=metadata.route,
                        target_animals=metadata.target_animals,
                        source_file=parsed.source_file,
                        manufacturer=metadata.manufacturer,
                        source_url=metadata.source_url
                    ))
            else:
                # Разбиваем длинную секцию на части
                sub_chunks = self._split_long_section(
                    section.content,
                    section.title
                )
                for sub_content in sub_chunks:
                    chunks.append(DrugChunkData(
                        content=sub_content,
                        section_type=section.section_type,
                        section_title=section.title,
                        trade_name=metadata.trade_name,
                        generic_name=metadata.generic_name,
                        drug_class=metadata.drug_class,
                        dosage_form=metadata.dosage_form,
                        route=metadata.route,
                        target_animals=metadata.target_animals,
                        source_file=parsed.source_file,
                        manufacturer=metadata.manufacturer,
                        source_url=metadata.source_url
                    ))

        return DrugChunksResult(
            trade_name=metadata.trade_name,
            generic_name=metadata.generic_name,
            target_animals=metadata.target_animals or [],
            chunks=chunks
        )

    def _split_long_section(
        self,
        content: str,
        section_title: str
    ) -> list[str]:
        """
        Разбиение длинной секции на части.

        Args:
            content: Содержимое секции
            section_title: Заголовок секции для добавления к каждой части

        Returns:
            Список частей с заголовком секции (без markdown ###)
        """
        # Пытаемся разбить по абзацам
        paragraphs = content.split('\n\n')

        chunks = []
        header = f"### {section_title}\n\n---\n\n"
        current_chunk = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # Если текущий чанк + абзац не превышает лимит, добавляем
            potential_chunk = current_chunk + ('\n\n' if current_chunk else '') + paragraph
            if len(header + potential_chunk) <= self.MAX_CHUNK_SIZE:
                current_chunk = potential_chunk
            else:
                # Сохраняем текущий чанк и начинаем новый
                if current_chunk:
                    chunks.append(header + current_chunk)
                current_chunk = paragraph

                # Если даже один абзац слишком длинный, разбиваем по предложениям
                if len(header + current_chunk) > self.MAX_CHUNK_SIZE:
                    sub_chunks = self._split_by_sentences(
                        paragraph,
                        section_title
                    )
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1].replace(header, '') if sub_chunks else ""

        # Добавляем последний чанк
        if current_chunk:
            chunks.append(header + current_chunk)

        return chunks

    def _split_by_sentences(
        self,
        content: str,
        section_title: str
    ) -> list[str]:
        """
        Разбиение по предложениям (fallback для очень длинных абзацев).

        Args:
            content: Содержимое для разбиения
            section_title: Заголовок секции для добавления к каждой части

        Returns:
            Список чанков с заголовком (без markdown ###)
        """


        # Простое разбиение по точке, восклицательному и вопросительному знакам
        sentences = re.split(r'(?<=[.!?])\s+', content)

        chunks = []
        header = f"### {section_title}\n\n---\n\n"
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            potential_chunk = current_chunk + (' ' if current_chunk else '') + sentence
            if len(header + potential_chunk) <= self.MAX_CHUNK_SIZE:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunks.append(header + current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(header + current_chunk)

        return chunks

    def export_to_csv(self, output_file: str | Path = 'instructions_chunks.csv') -> Path:
        """
        Обработка всех инструкций и экспорт чанков в CSV файл.

        Args:
            output_file: Путь к выходному CSV файлу

        Returns:
            Path к созданному файлу
        """
        output_path = Path(output_file)

        # Обрабатываем все инструкции
        all_results = self.process_all()

        if not all_results:
            logger.warning('Нет чанков для экспорта')
            return output_path

        # Собираем все чанки в плоский список
        db_records = []
        for result in all_results:
            for chunk in result.chunks:
                db_records.append({
                    'content': chunk.content,
                    'section_type': chunk.section_type,
                    'section_title': chunk.section_title,
                    'trade_name': chunk.trade_name,
                    'generic_name': chunk.generic_name or '',
                    'drug_class': chunk.drug_class or '',
                    'dosage_form': chunk.dosage_form or '',
                    'route': chunk.route or '',
                    'target_animals': ', '.join(chunk.target_animals) if chunk.target_animals else '',
                    'source_file': chunk.source_file,
                    'manufacturer': chunk.manufacturer or '',
                    'source_url': chunk.source_url or ''
                })

        # Записываем в CSV
        fieldnames = [
            'trade_name',
            'generic_name',
            'drug_class',
            'dosage_form',
            'route',
            'target_animals',
            'section_type',
            'section_title',
            'content',
            'source_file',
            'manufacturer',
            'source_url'
        ]

        with open(output_path, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                quoting=csv.QUOTE_MINIMAL
            )
            writer.writeheader()
            writer.writerows(db_records)

        logger.info(
            f'Экспортировано {len(db_records)} чанков '
            f'из {len(all_results)} инструкций в {output_path.absolute()}'
        )
        return output_path


def get_all_chunks_for_db() -> list[dict]:
    """
    Получение всех чанков в формате для вставки в БД.

    Returns:
        Список словарей с данными чанков
    """
    chunker = DrugChunker()
    all_results = chunker.process_all()

    db_records = []
    for result in all_results:
        for chunk in result.chunks:
            db_records.append({
                'content': chunk.content,
                'section_type': chunk.section_type,
                'section_title': chunk.section_title,
                'trade_name': chunk.trade_name,
                'generic_name': chunk.generic_name,
                'drug_class': chunk.drug_class,
                'dosage_form': chunk.dosage_form,
                'route': chunk.route,
                'target_animals': chunk.target_animals,
                'source_file': chunk.source_file,
                'manufacturer': chunk.manufacturer,
                'source_url': chunk.source_url
            })

    return db_records