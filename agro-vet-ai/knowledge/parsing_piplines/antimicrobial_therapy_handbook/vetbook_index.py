import re
import json

import fitz  # PyMuPDF


def pdf_to_text(input_path, output_path, start_page=655):
    doc = fitz.open(input_path)
    full_text = []
    
    for page_num in range(start_page - 1, len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("blocks", sort=True)  # sort=True для правильного порядка
        
        page_text = []
        for block in blocks:
            # Блок представляет собой кортеж: (x0, y0, x1, y1, ..., "текст")
            # Текст всегда находится в последнем элементе кортежа
            if isinstance(block[-1], str) and block[-1].strip():
                # Используем y0 (вертикальная координата) для сортировки
                page_text.append((block[1], block[-1].strip()))
        
        # Сортируем блоки по вертикальной позиции
        page_text.sort(key=lambda x: x[0])
        full_text.append("\n".join([text for _, text in page_text]))
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(full_text))
    
    print(f"Успешно сохранено: {output_path}")


def process_file(input_file):
    # Чтение файла и объединение строк по правилам
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Объединение строк с переносами
    merged_lines = []
    buffer = ""
    open_paren = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Пропускаем пустые строки
        if not stripped:
            continue
            
        # Подсчет скобок
        open_paren += stripped.count('(') - stripped.count(')')
        
        # Добавляем текущую строку в буфер
        if buffer:
            buffer += " " + stripped
        else:
            buffer = stripped
            
        # Проверяем условия окончания объединения
        if not (buffer.endswith(',') or open_paren > 0):
            merged_lines.append(buffer)
            buffer = ""
            open_paren = 0
    
    # Добавляем последний буфер, если остался
    if buffer:
        merged_lines.append(buffer)

    # Фильтрация нежелательных строк
    filtered_lines = []
    skip_patterns = [
        r'^=== page \d+ (left|right) ===$',
        r'^index \d+$',
        r'^\d+[\d\–\-\s,]*\d*\s*$',
        r'\\see separate heading',
        r'© \d{4}.*wiley.*',
        r'^\d+$',
        r'published \d{4} by',
        r'^john f\. prescott and patricia m\. dowling\. steeve giguère$',
        r'^inc\.$',
        r'^664 index$',
        r'^index$',
        r'^for details of antimicrobial susceptibility of individual$',
        r'^consult susceptibility tables bacterial and fungal species$',
        r'^and antimicrobial activity sections for individual drugs$',
        r'^xvii abbreviations$',
        r'^fifth edition\. edited by s antimicrobial therapy in veterinary medicine$',
        r'^united states$',
        r'^usage practices and benefits$',
        r'^u\.s\. food and drug administration, center for veterinary medicine, guidance$',
        r'^1/2$',
        r'^canadian $',
        # Общий паттерн для всех строк с "index" (улучшенный)
        r'^\s*\d{3,4}\s*index\s*$'
    ]
    
    for line in merged_lines:
        skip = False
        for pattern in skip_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                skip = True
                break
        if not skip:
            # Дополнительная фильтрация строк index
            if re.match(r'^\d+\s*index$', line, re.IGNORECASE):
                continue
            filtered_lines.append(line)

    # Обработка терминов
    all_terms = []
    for line in filtered_lines:
        # Удаление номеров страниц
        term = re.sub(r',\s*\d+.*$', '', line).strip()
        
        # Обработка "see"
        if 'see' in term.lower():
            # Разделяем по "see" и берем первую часть
            parts = re.split(r'\bsee\b', term, flags=re.IGNORECASE)
            term = parts[0].strip()
            
            # Удаляем запятые в конце
            term = re.sub(r',\s*$', '', term)
        
        # Пропускаем термины, начинающиеся с "see"
        if re.match(r'^\s*see\b', term, re.IGNORECASE):
            continue
            
        # Перестановка частей для терминов с одной запятой
        if term.count(',') == 1:
            part1, part2 = [p.strip() for p in term.split(',', 1)]
            term = f"{part2} {part1}"
        
        # Обработка скобок
        # Удаление скобок вокруг всего термина
        term = re.sub(r'^\((.*)\)$', r'\1', term)
        
        # Обработка случаев типа "(abc) def" -> "abc"
        if re.match(r'^\([^)]+\)\s+[\w\s]+$', term):
            term = re.sub(r'^\(([^)]+)\)\s+[\w\s]+$', r'\1', term)
        
        # Обработка случаев типа "(tables); clavulanic" -> "clavulanic"
        if ';' in term:
            parts = term.split(';')
            term = parts[-1].strip()
            # Удаление скобок в оставшейся части
            term = re.sub(r'[()]', '', term)
        
        # Общее удаление скобок
        term = re.sub(r'[()]', '', term)
        
        # Приведение к нижнему регистру
        term = term.lower()
        
        # Удаление лишних пробелов
        term = re.sub(r'\s+', ' ', term).strip()
        
        # Удаление одиночных символов и цифр
        if len(term) <= 1 or term.isdigit():
            continue
            
        # Добавление в список, если не пустой
        if term:
            all_terms.append(term)
    
    # Удаление дубликатов
    seen = set()
    unique_terms = []
    for term in all_terms:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)
    
    # Сортировка в алфавитном порядке
    unique_terms.sort()
    
    # Сохранение результатов в JSON
    with open('final_terms.json', 'w', encoding='utf-8') as f:
        json.dump(unique_terms, f, indent=2, ensure_ascii=False)
    
    return unique_terms
