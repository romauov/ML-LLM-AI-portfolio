import re


def fix_page_headers(pages: list[dict], chapters: dict) -> list[dict]:
    """
    Исправляет уровни заголовков в markdown страниц перед парсингом.

    Выполняет:
    1. Исправление уровней заголовков (Header 1 → Header 2 внутри нумерованных секций)
    2. Добавление названий глав к числовым параграфам (# 1 → # 1 Название главы)
    3. Удаление дублирующихся заголовков глав
    4. Преобразование заголовков-списков (# - Text) в обычные списки

    Эта функция должна вызываться ДО BookSplitter.extract_text(),
    чтобы исправленные заголовки правильно распарсились в метаданные чанков.

    Args:
        pages: Список страниц с markdown для исправления уровней
        chapters: Словарь глав из constants.py: {(start_page, end_page): "Название главы"}

    Returns:
        list[dict]: Список страниц с исправленным markdown
    """
    # Создаем словарь: номер страницы -> название главы
    page_to_chapter = {}
    for (start_page, end_page), chapter_name in chapters.items():
        for page_num in range(start_page, end_page):
            page_to_chapter[page_num] = chapter_name

    fixed_pages = []
    current_section_is_numbered = False
    current_chapter_name = None

    for page in pages:
        markdown = page['markdown']
        lines = markdown.split('\n')
        fixed_lines = []
        page_number = page.get('index', 0) + 1

        for line in lines:
            # Проверяем, является ли строка заголовком с дефисом (# - Text или ## - Text)
            if re.match(r'^#+\s*-\s*', line):
                list_item = re.sub(r'^#+\s*', '', line)
                fixed_lines.append(list_item)
                continue

            # Проверяем, является ли строка заголовком первого уровня
            if re.match(r'^#\s+', line) and not re.match(r'^##', line):
                header_text = re.sub(r'^#\s+', '', line).strip()
                is_number = re.match(r'^\d+$', header_text)

                if is_number:
                    current_section_is_numbered = True
                    chapter_name = page_to_chapter.get(page_number, '')
                    if chapter_name:
                        fixed_line = f"# {header_text} {chapter_name}"
                        fixed_lines.append(fixed_line)
                        current_chapter_name = chapter_name
                    else:
                        fixed_lines.append(line)
                        current_chapter_name = None
                else:
                    if current_section_is_numbered:
                        fixed_line = '##' + line[1:]
                        fixed_lines.append(fixed_line)
                    else:
                        fixed_lines.append(line)
            elif re.match(r'^##\s+', line):
                header2_text = re.sub(r'^##\s+', '', line).strip()
                if current_chapter_name and header2_text == current_chapter_name:
                    continue
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)

        fixed_page = page.copy()
        fixed_page['markdown'] = '\n'.join(fixed_lines)
        fixed_pages.append(fixed_page)

    return fixed_pages


def split_composite_tables(tables: list[dict]) -> list[dict]:
    """
    Разделяет составные таблицы (таблицы с несколькими header rows) на отдельные подтаблицы.

    Args:
        tables: Список таблиц для обработки

    Returns:
        list[dict]: Список таблиц после разделения
    """
    print("\nРазделение составных таблиц...")
    original_tables_count = len(tables)
    result_tables = []

    for table in tables:
        content = table['content']
        lines = content.split('\n')

        # Находим строки-разделители (header rows) с пустой первой ячейкой и строки с данными
        header_indices = []
        separator_index = None
        data_rows_count = 0

        for i, line in enumerate(lines):
            line_strip = line.strip()

            # Пропускаем пустые строки
            if not line_strip:
                continue

            # Проверяем, является ли строка markdown table row
            if line_strip.startswith('|') and line_strip.endswith('|'):
                cells = [cell.strip() for cell in line_strip.split('|')[1:-1]]

                # Находим строку-разделитель таблицы (| :--: | :--: |)
                if all(':--' in cell or '--:' in cell or ':---:' in cell for cell in cells if cell):
                    separator_index = i
                    continue

                # Проверяем, является ли это строкой-заголовком (первая ячейка пустая или только пробелы)
                if cells and not cells[0].strip():
                    header_indices.append(i)
                else:
                    # Считаем строки с данными (не пустые и не header)
                    data_rows_count += 1

        # Разделяем только если:
        # 1. Есть несколько header rows (> 1)
        # 2. Есть строки с данными между header rows (data_rows_count > 0)
        # 3. Первый header сразу после separator
        should_split = False
        if len(header_indices) > 1 and separator_index is not None:
            should_split = (
                data_rows_count > 0 and
                header_indices[0] <= separator_index + 1
            )

        if should_split:
            # Проверяем, что между header rows есть строки с данными
            for idx in range(len(header_indices) - 1):
                rows_between = header_indices[idx + 1] - header_indices[idx]
                if rows_between > 1:  # Есть строки между заголовками
                    should_split = True
                    break
            else:
                should_split = False

        if should_split:
            # Разделяем таблицу на подтаблицы
            for idx, header_idx in enumerate(header_indices):
                # Определяем диапазон строк для текущей подтаблицы
                end_idx = header_indices[idx + 1] if idx + 1 < len(header_indices) else len(lines)

                # Формируем содержимое подтаблицы
                subtable_lines = []

                # Добавляем заголовок
                subtable_lines.append(lines[header_idx])

                # Добавляем разделитель (separator row)
                if separator_index is not None and separator_index < len(lines):
                    subtable_lines.append(lines[separator_index])

                # Добавляем строки данных до следующего заголовка
                for i in range(header_idx + 1, end_idx):
                    line = lines[i].strip()

                    # Пропускаем separator row и пустые строки
                    if not line:
                        continue
                    if i == separator_index:
                        continue
                    # Пропускаем следующий заголовок
                    if i in header_indices and i != header_idx:
                        break

                    subtable_lines.append(lines[i])

                # Создаем новую таблицу
                result_tables.append({
                    'type': table['type'],
                    'name': table.get('name'),
                    'content': '\n'.join(subtable_lines),
                    'page_number': table['page_number']
                })
        else:
            # Если таблица не составная, добавляем как есть
            result_tables.append(table)

    print(f"Таблиц до разделения: {original_tables_count}, после: {len(result_tables)}")
    return result_tables