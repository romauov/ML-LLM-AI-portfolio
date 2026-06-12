import os
import json
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from openai import OpenAI

from config.config import Config
from app.db.db import build_db_url
from app.db.sqlalchemy_models import KnowledgeBaseChunk
from knowledge.parsing_piplines.antimicrobial_therapy_handbook.md_chunk_splitter import MDSplitter
from app.utils.settings import secrets as s

# --- Конфигурация ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SOURCE_DOCUMENT = "Antimicrobial Therapy in Veterinary Medicine, 5th Edition"
KNOWLEDGE_HANDBOOK_PATH = 'knowledge/data/antimicrobial_therapy_handbook'
BACKWARD_TOC_PATH = os.path.join(os.path.dirname(__file__), 'backward_toc.json')
KEY_TERMS_PATH = os.path.join(os.path.dirname(__file__), 'key_terms.json')
JSON_HANDBOOK = os.path.join(
    PROJECT_ROOT,
    KNOWLEDGE_HANDBOOK_PATH,
    f'{SOURCE_DOCUMENT}.json'
)

# Страницы, которые нужно исключить
EXCLUDED_PAGES = set(range(663, 684))

# Модель для создания эмбеддингов
EMBEDDING_MODEL = Config.from_yaml().llm_models.vsegpt.embedding


# --- Основные функции ---


def get_embedding(text: str, client: OpenAI) -> List[float]:
    """Получает векторное представление текста с помощью OpenAI API."""
    try:
        print(f"      (INFO) Векторизация чанка с помощью '{EMBEDDING_MODEL}'...")
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"      [ERROR] Ошибка при векторизации: {e}")
        return []


def find_keywords(text: str, key_terms: List[str]) -> List[str]:
    """Находит ключевые слова из списка в тексте."""
    found_keywords = []
    text_lower = text.lower()
    for term in key_terms:
        if term.lower() in text_lower:
            found_keywords.append(term)
    return found_keywords


def process_fragments():
    """
    Основная функция для обработки текстовых фрагментов, их векторизации
    и сохранения в базу данных.
    """
    print("--- Начало процесса векторизации ---")

    # 1. Загрузка вспомогательных данных
    print("1. Загрузка оглавления и ключевых слов...")
    toc = {}
    key_terms = []
    try:
        with open(BACKWARD_TOC_PATH, 'r', encoding='utf-8') as f:
            toc = json.load(f)
    except FileNotFoundError:
        print(f"   [WARN] Оглавление не найдено: {BACKWARD_TOC_PATH}. Будет использовано значение 'Unknown Chapter'.")
    try:
        with open(KEY_TERMS_PATH, 'r', encoding='utf-8') as f:
            key_terms = json.load(f)
    except FileNotFoundError:
        print(f"   [WARN] Ключевые термины не найдены: {KEY_TERMS_PATH}. Поиск ключевых слов будет пропущен.")
    print("   ...данные загружены.")

    print("2. Настройка подключения к базе данных...")
    db_url = build_db_url()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    print("   ...подключение настроено.")

    print(f"3. Инициализация клиента OpenAI для модели '{EMBEDDING_MODEL}'...")
    openai_client = OpenAI(
        api_key=s.vsegpt_api_key,
        base_url=s.vsegpt_base_url
    )
    print("   ...клиент инициализирован.")

    print("4. Начало обработки текстовых фрагментов...")
    # Считываем json handbook
    with open(JSON_HANDBOOK, "r") as f:
        data = json.load(f)

    page_text_data, page_other_data = [], []
    chunk_number = 1
    for page in data['pages']:
        page_number = page.get('page_number')
        if not page_number.isdigit():
            print(f"Пропуск страницы {page_number} (исключена).")
            continue

        page_number = int(page_number)
        if page_number in EXCLUDED_PAGES:
            print(f"   - Пропуск страницы {page_number} (исключена).")
            continue

        page_number = int(page_number)
        content = page.get('markdown')
        if not content.strip():
            print(f"     - Страница пустая, пропуск.")
            continue

        chapter_title = toc.get(str(page_number), "Unknown Chapter")
        text_chunks, figure_chunks, table_chunks = MDSplitter(content).split_text_with_tables_and_figures()

        for text_chunk in text_chunks:
            if not text_chunk.metadata and len(page_text_data) > 0:
                previous_page_last_chunk = page_text_data.pop(-1)
                previous_content = previous_page_last_chunk['content']
                previous_page_last_chunk.update({'content': f'{previous_content} {text_chunk.page_content}'})
                page_text_data.append(previous_page_last_chunk)
            else:
                data = {
                    'content': text_chunk.page_content,
                    'page_number': page_number,
                    'chapter_title': chapter_title,
                    'chunk_number': chunk_number,
                    'type': 'text'
                }
                if text_chunk.metadata.get('Header 2') == 'Bibliography':
                    data.update({'type': 'bibliography'})
                page_text_data.append(data)
                chunk_number += 1

        for table_chunk in table_chunks:
            if not table_chunk.metadata.get('name') and len(page_other_data):
                previous_page_last_chunk = page_other_data.pop(-1)
                previous_content = previous_page_last_chunk['content']
                previous_page_last_chunk.update({'content': f'{previous_content}\n{table_chunk.page_content}'})
                page_other_data.append(previous_page_last_chunk)
            else:
                page_other_data.append({
                    'content': table_chunk.page_content,
                    'page_number': page_number,
                    'chapter_title': chapter_title,
                    'chunk_number': chunk_number,
                    **table_chunk.metadata
                })
                chunk_number += 1

        for figure_chunk in figure_chunks:
            page_other_data.append({
                'content': figure_chunk.page_content,
                'page_number': page_number,
                'chapter_title': chapter_title,
                'chunk_number': chunk_number,
                **figure_chunk.metadata
            })
            chunk_number += 1

    for chunk_data in [*page_text_data, *page_other_data]:
        try:
            content = chunk_data['content']
            page_number = chunk_data['page_number']
            chunk_number = chunk_data['chunk_number']
            chapter_title = chunk_data['chapter_title']
            keywords = find_keywords(content, key_terms)
            embedding = get_embedding(content, openai_client)
            if not embedding:
                print(
                    f"[WARNING] Не удалось создать эмбеддинг для страницы {page_number} chunk_number {chunk_number}. Пропуск.")
                continue

            content_type = chunk_data.get('type')
            content_name = None
            if content_type in ('figure', 'table'):
                content_name = chunk_data.get('name')

            # Создание объекта и добавление в сессию
            new_chunk = KnowledgeBaseChunk(
                content=content,
                content_type=content_type,
                content_name=content_name,
                embedding=embedding,
                page_number=page_number,
                chunk_number=chunk_number,
                chapter_title=chapter_title,
                keywords=keywords,
                source_document=SOURCE_DOCUMENT
            )
            session.add(new_chunk)

        except Exception as e:
            print(f"   [ERROR] Не удалось обработать страницу: {e}")
            session.rollback()  # Откатываем транзакцию, если была ошибка с одним файлом
            continue

    print("5. Сохранение всех изменений в базе данных...")
    try:
        session.commit()
        print("   ...изменения успешно сохранены.")
    except Exception as e:
        print(f"[ERROR] Ошибка при коммите в БД: {e}")
        session.rollback()
    finally:
        session.close()
        print("   ...сессия с БД закрыта.")

    print("--- Процесс векторизации завершен ---")
