import os
import json

from knowledge.parsing_piplines.avian_pathology.constants import PROJECT_ROOT, KNOWLEDGE_PATH, JSON_BOOK, IMAGE_PAGES
from knowledge.utils.vsegpt_pdf_ocr_utils import handle_images_from_json


OUTPUT_DIR = os.path.join(PROJECT_ROOT, KNOWLEDGE_PATH, 'parsed_images')

if __name__ == '__main__':
    pages_to_extract = set(IMAGE_PAGES)

    with open(JSON_BOOK, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Фильтруем страницы
    # В JSON используется поле 'index' (нумерация с 0), а в CHAPTERS - обычная нумерация (с 1)
    filtered_pages = []
    for page in data['pages']:
        page_index = page.get('index', None)
        try:
            if page_index is not None:
                page_num = page_index + 1
                if page_num in pages_to_extract:
                    filtered_pages.append(page)
        except (ValueError, TypeError):
            continue

    print(f"Filtered {len(filtered_pages)} pages out of {len(data['pages'])} total pages")

    # Создаем временный JSON с отфильтрованными страницами
    filtered_data = {
        'pages': filtered_pages
    }

    temp_json_path = os.path.join(PROJECT_ROOT, KNOWLEDGE_PATH, 'temp_filtered.json')

    with open(temp_json_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)

    handle_images_from_json(temp_json_path, OUTPUT_DIR)

    # Удаляем временный файл
    os.remove(temp_json_path)