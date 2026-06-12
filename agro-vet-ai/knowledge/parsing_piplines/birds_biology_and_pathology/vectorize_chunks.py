import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import KnowledgeBaseChunk
from app.llm.providers.llm_provider import LLMProvider
from knowledge.utils.book_splitter.book_splitter import BookSplitter
from knowledge.parsing_piplines.birds_biology_and_pathology.constants import JSON_BOOK, CHAPTERS, EXCLUDED_PAGES, \
    SOURCE_DOCUMENT


def get_chapter(page_number):
    for (start, end), value in CHAPTERS.items():
        if start <= page_number < end:
            return value


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

    print(f"\n{'=' * 80}")
    print("ОБРАБОТКА КНИГИ С ПОМОЩЬЮ BOOK SPLITTER:")
    print(f"{'=' * 80}\n")

    splitter = BookSplitter(
        pages=pages,
        table_description_regex=r'Таблица \d{1,3}\.',
        image_description_regex=r'^Рис\.?\s*\d{1,3}[\.\,\s]',
        to_drop_line_regex=r'^\[\^0\]',
        text_chunk_size=2000
    )

    texts, tables, images = (splitter
                             .before_delete_newlines_symbol_at_table_cells()
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

    # Batch commit каждые N чанков для надёжности
    BATCH_SIZE = 50
    saved_count = 0
    failed_count = 0

    for chunk_number, chunk in enumerate(all_chunks, start=1):
        try:
            chunk_type = chunk['type']
            chunk_name = chunk.get('name', 'N/A')
            page_num = chunk['page_number']

            print(f"[{chunk_number}/{len(all_chunks)}] Обработка {chunk_type} чанка "
                  f"(стр. {page_num}, название: {chunk_name})")

            # Векторизация контента
            print(f"  → Векторизация контента...")
            embedding = llm_provider.vectorize(chunk['content'])
            print(f"  ✓ Векторизация завершена")

            # Создание записи в БД
            print(f"  → Добавление в сессию БД...")
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
            saved_count += 1
            print(f"  ✓ Добавлен в сессию\n")

            # Сохранение пакетов чанков в БД
            if chunk_number % BATCH_SIZE == 0:
                print(f"\n{'=' * 80}")
                print(f"BATCH COMMIT: Сохранение чанков {chunk_number - BATCH_SIZE + 1}-{chunk_number}...")
                print(f"{'=' * 80}")
                try:
                    session.commit()
                    print(f"Успешно сохранено {BATCH_SIZE} чанков в БД")
                    print(f"    Всего сохранено: {chunk_number}/{len(all_chunks)}")
                    print(f"    Прогресс: {chunk_number / len(all_chunks) * 100:.1f}%")
                    print(f"{'=' * 80}\n")
                except Exception as e:
                    print(f"[ERROR] Ошибка при batch commit: {e}")
                    print(f"    Откатываем последние {BATCH_SIZE} чанков")
                    session.rollback()
                    saved_count -= BATCH_SIZE
                    failed_count += BATCH_SIZE
                    print(f"{'=' * 80}\n")
                    print("[STOP] Остановка работы из-за ошибки коммита.")
                    session.close()
                    raise  # Re-raise the exception to stop the program

        except Exception as e:
            print(f"✗ [ERROR] Не удалось обработать чанк {chunk_number}: {e}")
            failed_count += 1
            saved_count -= 1
            continue

    # Финальный commit для оставшихся чанков
    remaining = len(all_chunks) % BATCH_SIZE
    print(f"\n{'=' * 80}")
    print(f"ФИНАЛЬНЫЙ COMMIT: Сохранение последних {remaining} чанков...")
    print(f"{'=' * 80}")
    try:
        session.commit()
        print(f"Финальный commit успешен!")
        print(f"\n{'=' * 80}")
        print(f"ИТОГОВАЯ СТАТИСТИКА:")
        print(f"{'=' * 80}")
        print(f"Всего чанков для обработки: {len(all_chunks)}")
        print(f"Успешно сохранено: {saved_count}")
        print(f"Ошибок при обработке: {failed_count}")
        print(f"Процент успеха: {saved_count / len(all_chunks) * 100:.1f}%")
        print(f"{'=' * 80}")
    except Exception as e:
        print(f"[ERROR] Ошибка при финальном коммите в БД: {e}")
        session.rollback()
    finally:
        session.close()
        print("...сессия с БД закрыта.")
        print(f"{'=' * 80}")


if __name__ == "__main__":
    process_chunks()
