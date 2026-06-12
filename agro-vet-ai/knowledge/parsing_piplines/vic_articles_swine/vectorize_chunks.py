import json
import os
import re
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from app.db.db import build_db_url
from app.db.sqlalchemy_models import KnowledgeBaseChunk, SourceDocument, Images
from app.llm.providers.llm_provider import LLMProvider
from knowledge.parsing_piplines.vic_articles_swine.constants import JSON_ARTICLES, IMAGES_PATH


def normalize_date(date_str: str | None) -> str | None:
    """Возвращает строку даты если год в диапазоне 1980–2026, иначе None.

    Исходные данные содержат артефакты скрейпинга: '77-67-67', '1931 г.',
    числовые ID вроде '109472', '6379 г', '8325 г'.
    """
    if not date_str:
        return None
    match = re.search(r'\b(\d{4})\b', date_str)
    if match and 1980 <= int(match.group(1)) <= 2026:
        return ' '.join(date_str.split())
    return None


def build_meta_info(article: dict) -> str:
    """Формирует строку метаданных для source_document.contents."""
    author = article.get('author') or 'не указан'
    journal = article.get('journal') or 'не указан'
    date = normalize_date(article.get('date'))

    lines = [
        f"Автор: {author}",
        f"Журнал: {journal}",
    ]
    if date:
        lines.append(f"Дата: {date}")
    return '\n'.join(lines)


def build_chunk_prefix(article: dict) -> str:
    """Компактный заголовок метаданных, добавляемый к каждому чанку.

    Позволяет LLM видеть источник прямо в тексте чанка при RAG-поиске.
    Формат: [Статья: «...» | Автор: ... | Журнал: ... | Дата: ...]
    """
    parts = [f"Статья: «{article['title'].strip()}»"]
    author = article.get('author')
    if author:
        parts.append(f"Автор: {author}")
    journal = article.get('journal')
    if journal:
        parts.append(f"Журнал: {journal}")
    date = normalize_date(article.get('date'))
    if date:
        parts.append(f"Дата: {date}")
    return '[' + ' | '.join(parts) + ']\n'


def process_articles():
    """Обработка статьи."""

    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()
    llm_provider = LLMProvider()

    with open(JSON_ARTICLES, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    # Настройка сплиттеров
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)

    skipped_large = []
    skipped_existing = []
    failed = []

    # Индекс изображений: server_filename -> локальный полный путь.
    # Локальные файлы называются {prefix_статьи}_{server_filename}
    images_by_server_name = {}
    if os.path.isdir(IMAGES_PATH):
        for _fname in os.listdir(IMAGES_PATH):
            _full = os.path.join(IMAGES_PATH, _fname)
            images_by_server_name[_fname] = _full # точное совпадение
            images_by_server_name[_fname.rsplit('_', 1)[-1]] = _full  # серверная часть

    for article in articles:
        title = article['title'].strip()

        # 1. Пропускаем статьи с аномально большим контентом
        content = article.get('content', '')

        # 2. Проверяем, существует ли уже такой источник
        stmt = select(SourceDocument).where(SourceDocument.name == title)
        existing_source = session.execute(stmt).scalar_one_or_none()
        if existing_source:
            print(f"[SKIP] Уже существует (ID: {existing_source.id}): '{title[:70]}'")
            skipped_existing.append(title)
            continue

        print(f"\n>>> Добавление: {title[:80]}")

        chunk_prefix = build_chunk_prefix(article)

        # 3. Создаем SourceDocument
        # Дата нормализуется: значения до 1980 г. и артефакты скрейпинга → None
        new_source = SourceDocument(
            name=title,
            language='ru',
            contents=build_meta_info(article),
        )
        session.add(new_source)
        session.flush()
        source_id = new_source.id

        # 4. Нарезка контента
        sections = md_splitter.split_text(content)
        chunk_number_in_article = 1

        article_failed = False
        for section in sections:
            sub_chunks = text_splitter.split_documents([section])

            for sub_chunk in sub_chunks:
                chunk_content = sub_chunk.page_content

                # Поиск изображений
                image_matches = re.findall(r'!\[.*?\]\((.*?)\)', chunk_content)

                # Очистка текста
                clean_content = re.sub(r'!\[.*?\]\(.*?\)', '', chunk_content).strip()
                if not clean_content:
                    clean_content = f"Изображение из статьи '{title}'"

                chapter_title = sub_chunk.metadata.get('Header 2', sub_chunk.metadata.get('Header 1', title))
                content_with_prefix = chunk_prefix + clean_content

                try:
                    print(f"  Добавление чанка {chunk_number_in_article}...")
                    embedding = llm_provider.vectorize(clean_content)

                    kb_chunk = KnowledgeBaseChunk(
                        content=content_with_prefix,
                        content_type='text',
                        embedding=embedding,
                        chunk_number=chunk_number_in_article,
                        chapter_title=chapter_title,
                        source_document_id=source_id,
                    )
                    session.add(kb_chunk)
                    session.flush()

                    # Сохранение изображений.
                    # Markdown содержит серверные пути (/upload/medialibrary/.../hash.png),
                    # локальные файлы именованы {prefix_статьи}_{hash.png}.
                    # Поиск ведётся по индексу images_by_server_name.
                    for img_rel_path in image_matches:
                        server_filename = os.path.basename(img_rel_path)
                        img_full_path = images_by_server_name.get(server_filename)

                        if img_full_path:
                            with open(img_full_path, 'rb') as img_f:
                                img_data = img_f.read()

                            if len(img_data) <= 4 * 1024:
                                continue  # пропускаем иконки и заглушки

                            local_img_filename = os.path.basename(img_full_path)
                            img_chunk = KnowledgeBaseChunk(
                                content=f"Изображение {local_img_filename} из статьи '{title}'",
                                content_type='figure',
                                content_name=local_img_filename,
                                embedding=embedding,
                                chunk_number=chunk_number_in_article,
                                chapter_title=chapter_title,
                                source_document_id=source_id,
                            )
                            session.add(img_chunk)
                            session.flush()

                            image_record = Images(
                                chunk_id=img_chunk.id,
                                source_document=title,
                                image_data=img_data,
                            )
                            session.add(image_record)
                            print(f"    - Изображение {local_img_filename} добавлено.")

                    chunk_number_in_article += 1

                except Exception as e:
                    print(f"[ERROR] Статья '{title[:60]}', чанк {chunk_number_in_article}: {e}")
                    session.rollback()
                    article_failed = True
                    break

            if article_failed:
                break

        if article_failed:
            failed.append(title)
            continue

        session.commit()
        print(f"  ✓ Статья добавлена ({chunk_number_in_article - 1} чанков).")

    session.close()

    print("\n" + "=" * 60)
    print("ИТОГ:")
    print(f"  Пропущено (уже в БД):        {len(skipped_existing)}")
    print(f"  Пропущено (большой контент): {len(skipped_large)}")
    if skipped_large:
        for t in skipped_large:
            print(f"    - {t[:80]}")
    print(f"  Ошибки при обработке:        {len(failed)}")
    if failed:
        for t in failed:
            print(f"    - {t[:80]}")
    print("=" * 60)

if __name__ == "__main__":
    process_articles()
