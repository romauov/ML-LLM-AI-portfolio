import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import KnowledgeBaseChunk
from app.llm.providers.llm_provider import LLMProvider
from knowledge.utils.book_splitter.book_splitter import BookSplitter
from knowledge.parsing_piplines.poultry_health_guide.constants import JSON_BOOK, CHAPTERS, EXCLUDED_PAGES, \
    SOURCE_DOCUMENT
from knowledge.parsing_piplines.poultry_health_guide.utils import preprocess_remove_text_between_h1_and_h2


def get_chapter(page_number):
    """Получение названия главы по номеру страницы"""
    for (start, end), value in CHAPTERS.items():
        if start <= page_number < end:
            return value
    return "Неизвестная глава"


def process_chunks():
    """
    Основная функция для обработки текстовых фрагментов, их векторизации
    и сохранения в базу данных.
    """

    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    llm_provider = LLMProvider()
    print("Загрузка данных из JSON файла...")
    with open(JSON_BOOK, "r", encoding='utf-8') as f:
        data = json.load(f)

    # Фильтрация исключенных страниц
    pages = [page for page in data['pages'] if page.get('index') + 1 not in EXCLUDED_PAGES]

    # Предобработка: удаление текста между Header 1 и Header 2
    pages = preprocess_remove_text_between_h1_and_h2(pages)

    print(f"\n{'=' * 80}")
    print("ОБРАБОТКА КНИГИ С ПОМОЩЬЮ BOOK SPLITTER:")
    print(f"{'=' * 80}\n")

    splitter = BookSplitter(
        pages=pages,
        table_description_regex=r'^(Table (?!16i\.1\.)\d{1,3}[ivxlcdm]*\.?\d*\.?)',
        image_description_regex=r'^(Fig\.?\s*\d{1,3}[ivxlcdm]*\.?\d*\.?|Figs 20\.15 and 20\.16\.|Table 16i\.1\.)',
        to_drop_line_regex=r'(\[\^\d+\]\.?)',
        text_chunk_size=2000
    )

    texts, tables, images = (splitter
                             .extract_table()
                             .extract_image()
                             .extract_text()
                             .after_combine_single_table_separated_by_diff_pages()
                             .after_combine_single_text_separated_by_diff_pages()
                             .after_split_text_chunks()
                             .after_get_chunks())

    # Векторизация и сохранение в БД
    print(f"{'=' * 80}")
    print("ВЕКТОРИЗАЦИЯ И СОХРАНЕНИЕ В БД:")
    print(f"{'=' * 80}\n")

    all_chunks = [*texts, *tables, *images]

    for chunk_number, chunk in enumerate(all_chunks, start=1):
        try:
            chunk_type = chunk['type']
            chunk_name = chunk.get('name', 'N/A')
            page_num = chunk['page_number']

            print(f"[{chunk_number}/{len(all_chunks)}] Обработка {chunk_type} чанка "
                  f"(стр. {page_num}, название: {chunk_name})")

            embedding = llm_provider.vectorize(chunk['content'])
            new_chunk = KnowledgeBaseChunk(
                content=chunk['content'],
                content_type=chunk['type'],
                content_name=chunk.get('name', None),
                embedding=embedding,
                page_number=chunk['page_number'],
                chunk_number=chunk_number,
                chapter_title=get_chapter(chunk['page_number']),
                source_document=SOURCE_DOCUMENT
            )
            session.add(new_chunk)

        except Exception as e:
            print(f"✗ [ERROR] Не удалось обработать чанк {chunk_number}: {e}")
            continue

    print(f"\n{'=' * 80}")
    print(f"ФИНАЛЬНЫЙ COMMIT: Сохранение всех чанков...")
    print(f"{'=' * 80}")
    try:
        session.commit()
        print(f"Финальный commit успешен!")
        print(f"\n{'=' * 80}")
        print(f"ИТОГОВАЯ СТАТИСТИКА:")
        print(f"{'=' * 80}")
        print(f"Всего чанков для обработки: {len(all_chunks)}")
        print(f"Успешно сохранено: {len(all_chunks)}")
        print(f"{'=' * 80}")
    except Exception as e:
        print(f"[ERROR] Ошибка при финальном коммите в БД: {e}")
        session.rollback()
    finally:
        session.close()
        print("...сессия с БД закрыта.")
        print(f"{'=' * 80}")


if __name__ == '__main__':
    process_chunks()
