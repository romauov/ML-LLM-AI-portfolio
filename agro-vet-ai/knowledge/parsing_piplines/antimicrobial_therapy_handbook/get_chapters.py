import os
import json


def is_arabic(s):
    return s.isdigit()


def is_roman(s):
    roman_symbols = {'I', 'V', 'X', 'L', 'C', 'D', 'M'}
    s_upper = s.upper()
    return all(char in roman_symbols for char in s_upper) and s_upper


def roman_to_int(s):
    """Конвертирует римское число в целое (для сортировки)"""
    s = s.upper()
    rom_val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    int_val = 0
    for i in range(len(s)):
        if i > 0 and rom_val[s[i]] > rom_val[s[i - 1]]:
            int_val += rom_val[s[i]] - 2 * rom_val[s[i - 1]]
        else:
            int_val += rom_val[s[i]]
    return int_val


def int_to_roman(n):
    """Конвертирует целое число в римское (для диапазона i-xvii)"""
    roman_numerals = {
        1: 'i', 2: 'ii', 3: 'iii', 4: 'iv', 5: 'v',
        6: 'vi', 7: 'vii', 8: 'viii', 9: 'ix', 10: 'x',
        11: 'xi', 12: 'xii', 13: 'xiii', 14: 'xiv', 15: 'xv',
        16: 'xvi', 17: 'xvii'
    }
    return roman_numerals.get(n, '')


def build_and_save_toc_dictionaries():
    filenames = ['page_v.txt', 'page_vi.txt', 'page_vii.txt']
    base_dir = 'knowledge/data/antimicrobial_therapy_handbook/converted_to_txt'
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    forward_dict = {}
    backward_dict = {}

    # Собираем все записи из файлов
    all_entries = []
    for filename in filenames:
        filepath = os.path.join(base_dir, filename)
        if not os.path.exists(filepath):
            print(f"Файл не найден: {filepath}")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line == "Contents":
                    continue

                words = line.split()
                if len(words) < 2:
                    continue

                last_word = words[-1]
                if is_arabic(last_word) or is_roman(last_word):
                    title = ' '.join(words[:-1])
                    page = last_word

                    # Добавляем в прямой словарь
                    forward_dict[title] = page

                    # Сохраняем запись для обработки
                    all_entries.append((title, page))

    # Разделяем записи на римские и арабские
    roman_entries = []
    arabic_entries = []

    for title, page in all_entries:
        if is_roman(page):
            # Конвертируем в число для сравнения
            num = roman_to_int(page)
            roman_entries.append((num, title, page))
        elif is_arabic(page):
            num = int(page)
            arabic_entries.append((num, title, page))

    # Сортируем по числовому значению
    roman_entries.sort(key=lambda x: x[0])
    arabic_entries.sort(key=lambda x: x[0])

    # Обработка римских страниц (i-xvii)
    current_title = None
    for num in range(1, 18):  # От 1 до 17 включительно
        page_str = int_to_roman(num)

        # Ищем последнюю запись с номером <= текущему
        for r_num, title, orig_page in roman_entries:
            if r_num <= num:
                current_title = title
            else:
                break

        # Если нашли заголовок, добавляем в словарь
        if current_title:
            backward_dict[page_str] = current_title

    # Обработка арабских страниц (1-683)
    current_title = None
    for num in range(1, 684):
        page_str = str(num)

        # Ищем последнюю запись с номером <= текущему
        for a_num, title, orig_page in arabic_entries:
            if a_num <= num:
                current_title = title
            else:
                break

        # Если нашли заголовок, добавляем в словарь
        if current_title:
            backward_dict[page_str] = current_title

    # Сохраняем прямой словарь
    forward_path = os.path.join(output_dir, 'forward_toc.json')
    with open(forward_path, 'w', encoding='utf-8') as f:
        json.dump(forward_dict, f, ensure_ascii=False, indent=2)
    # print(f"Прямой словарь сохранен в: {forward_path}")

    # Сохраняем обратный словарь
    backward_path = os.path.join(output_dir, 'backward_toc.json')
    with open(backward_path, 'w', encoding='utf-8') as f:
        json.dump(backward_dict, f, ensure_ascii=False, indent=2)
    # print(f"Обратный словарь сохранен в: {backward_path}")

    return forward_dict, backward_dict
