import json
import os
import re
import requests
import base64

import pdfplumber
from collections import OrderedDict

from app.utils.settings import secrets as s

# Словарь для замены аббревиатур
ABBREVIATIONS = OrderedDict([
    (r'q\s*(\d+)\s*h', r'Every \1 hours,'),
    ('MIC', 'minimum inhibitory concentration'),
    ('MBC', 'minimum bactericidal concentration'),
    ('PO', 'per os, oral administration'),
    ('IM', 'intramuscular administration'),
    ('IV', 'intravenous administration'),
    ('SC', 'subcutaneous administration'),
    ('SID', 'single daily administration'),
    ('BID', 'twice-daily administration (every 12 hours)'),
    ('TID', '3 times daily administration (every 8 hours)'),
    ('QID', '4 times daily administration (every 6 hours)')
])

# Маппинг первых 13 страниц
ROMAN_MAPPING = {
    1: 'ii', 2: 'iii', 3: 'iv', 4: 'v',
    5: 'vi', 6: 'vii', 7: 'ix', 8: 'x',
    9: 'xi', 10: 'xii', 11: 'xiii', 12: 'xv',
    13: 'xvii',
}


def replace_abbreviations(text):
    """Заменяет аббревиатуры в тексте на полные формы"""
    for pattern, replacement in ABBREVIATIONS.items():
        text = re.sub(
            r'\b' + pattern + r'\b',
            replacement,
            text,
            flags=re.IGNORECASE
        )
    return text


def extract_page_number(text, current_book_page):
    """Извлекает номер страницы из текста с учетом структуры документа"""
    if not text:
        return None

    lines = text.split('\n')
    candidates = []

    # Ищем в верхних строках (первые 3 строки)
    for line in lines[:3]:
        # Игнорируем строки с явно не номером страницы
        if re.search(r'figure|таблица|chapter|глава|section|references|\d+\.\d+', line, re.IGNORECASE):
            continue

        # Ищем числа в начале или конце строки
        match_start = re.search(r'^\s*(\d{1,3})\b', line)
        match_end = re.search(r'\b(\d{1,3})\s*$', line)

        if match_start:
            num = int(match_start.group(1))
            candidates.append(num)
        if match_end:
            num = int(match_end.group(1))
            candidates.append(num)

    # Ищем в нижних строках (последние 3 строки)
    for line in lines[-3:]:
        # Игнорируем строки с явно не номером страницы
        if re.search(r'figure|таблица|chapter|глава|section|references|\d+\.\d+', line, re.IGNORECASE):
            continue

        # Для нижних строк ищем только в конце
        match_end = re.search(r'\b(\d{1,3})\s*$', line)
        if match_end:
            num = int(match_end.group(1))
            candidates.append(num)

    # Фильтруем кандидатов по логичности
    valid_candidates = []
    for num in candidates:
        # Номер должен быть в разумных пределах
        if 1 <= num <= 999:
            # Если у нас уже есть текущий номер, проверяем последовательность
            if current_book_page:
                if num > current_book_page and num <= current_book_page + 5:
                    valid_candidates.append(num)
            else:
                # Для первой арабской страницы
                if num >= 2:
                    valid_candidates.append(num)

    if valid_candidates:
        # Выбираем ближайший к ожидаемому
        if current_book_page:
            return min(valid_candidates, key=lambda x: abs(x - (current_book_page + 1)))
        else:
            return min(valid_candidates)

    return None


def handle_extracted_page_number(extracted_num, current_book_page, i):
    """Обработка извлеченных номеров страниц"""
    # Обработка нумерации с учетом пропущенных страниц
    if extracted_num is None:
        # Если номер не найден, используем инкремент
        if current_book_page is None:
            page_num = 2  # Первая арабская страница
        else:
            page_num = current_book_page + 1
    else:
        # Проверяем логичность номера
        if current_book_page is not None:
            if extracted_num < current_book_page or extracted_num > current_book_page + 5:
                # Если номер нелогичен, используем инкремент
                page_num = current_book_page + 1
                print(f"  Предупреждение: нелогичный номер {extracted_num} после {current_book_page} "
                      f"на PDF-странице {i + 1}. Используем {page_num}")
            else:
                page_num = extracted_num
        else:
            page_num = extracted_num
    return page_num


def add_page_number_to_json(json_path, source_pdf_path):
    """Добавление номеров страниц в json файл"""
    page_numbers = []
    try:
        with pdfplumber.open(source_pdf_path) as pdf:
            num_pages = len(pdf.pages)
            print(f"Извлечение номеров страниц из: {os.path.basename(source_pdf_path)} ({num_pages} страниц)")

            # Для отслеживания правильной нумерации
            current_book_page = None  # Текущий номер книжной страницы

            for i, page in enumerate(pdf.pages):
                # Определяем номер страницы для имени файла
                if i < 13:  # Первые 13 страниц
                    page_num = ROMAN_MAPPING[i + 1]
                else:
                    text = page.extract_text() or ""
                    # Извлекаем номер страницы из контента
                    extracted_num = extract_page_number(text, current_book_page)
                    page_num = handle_extracted_page_number(extracted_num, current_book_page, i)
                    current_book_page = page_num
                page_numbers.append(page_num)

                print(f"PDF-страница {i + 1} -> Книжная страница {page_num}")

        # добавляем номера страниц в json файл
        with open(json_path, "r") as f:
            data = json.load(f)

        for i, page_number in enumerate(page_numbers):
            data['pages'][i].update({'page_number': str(page_number)})

        with open(json_path, "w") as f:
            json.dump(data, f, indent=4)

    except Exception as e:
        print(f"Критическая ошибка: {e}")


def ocr_pdf_to_json(pdf_path, output_dir):
    """
    Парсинг pdf в json файл, с учетом картинок, таблиц и двухколоночных страниц.
    Примечание: 1 страница 0.5 рублей
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(pdf_path, "rb") as file:
        encoded_file = base64.b64encode(file.read()).decode('utf-8')

    name = pdf_path.split('/')[-1].split('.')[0]
    response = requests.post(
        f"{s.vsegpt_base_url}/extract_text",
        headers={
            "Authorization": f"Bearer {s.vsegpt_api_key}"
        },
        json={
            "encoded_base64_file": encoded_file,
            "filename": f"{name}.pdf",
            "model": "utils/pdf-ocr-1.0",
            "return_images": True,
        }
    )

    with open(os.path.join(output_dir, f'{name}.json'), "w") as f:
        json.dump(response.json(), f, indent=4)
