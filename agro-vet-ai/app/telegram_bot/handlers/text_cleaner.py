import re


def clean_text(text: str) -> str:
    """
    Подготавливает текст для Telegram с читаемым форматированием.
    Сохраняет HTML-теги, добавляет пустые строки между блоками.
    """
    if not text:
        return ""

    # Убираем markdown теги, конвертируем в HTML
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__([^_]+)__', r'<u>\1</u>', text)
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Заменяем теги <div> и <p> на переносы строк
    text = re.sub(r'</?(div|p)[^>]*>', '\n', text)

    # Заменяем <br> теги на переносы строк
    text = re.sub(r'<br\s*/?>', '\n', text)

    # Заменяем <hr> теги на разделитель
    text = re.sub(r'<hr[^>]*>', '\n━━━━━━━━━━━━━━━━━━━━━━━━\n', text)

    # Конвертируем HTML списки в Telegram-совместимый формат
    # Обрабатываем ненумерованные списки
    text = re.sub(r'<ul>\s*<li>', '• ', text)
    text = re.sub(r'</li>\s*<li>', '\n• ', text)
    text = re.sub(r'</li>\s*</ul>', '', text)

    # Обрабатываем нумерованные списки
    lines = text.split('\n')
    new_lines = []
    in_ol = False
    ol_counter = 1

    for line in lines:
        if '<ol>' in line:
            in_ol = True
            ol_counter = 1
            line = line.replace('<ol>', '')
        elif '</ol>' in line:
            in_ol = False
            line = line.replace('</ol>', '')

        if in_ol and '<li>' in line:
            # Обрабатываем нумерованный список
            if 'value="' in line:
                match = re.search(r'value="(\d+)"', line)
                if match:
                    ol_counter = int(match.group(1))
                    line = line.replace(match.group(0), '')
            line = line.replace('<li>', f'{ol_counter}. ')
            ol_counter += 1
        elif '<li>' in line:
            # Обрабатываем ненумерованный список
            line = line.replace('<li>', '• ')

        # Убираем теги </li> везде
        line = line.replace('</li>', '')

        new_lines.append(line)

    text = '\n'.join(new_lines)

    # Убираем отступы в начале строк, заменяем дефисы на буллеты
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- ') or stripped.startswith('– '):
            cleaned_lines.append('• ' + stripped[2:])
        else:
            cleaned_lines.append(stripped)

    text = '\n'.join(cleaned_lines)

    # Добавляем пустую строку после нумерованных пунктов (1. <b>Название</b>)
    text = re.sub(r'(\d+\.\s+<b>[^<]+</b>[^\n]*)\n(?!\n)', r'\1\n\n', text)

    # Добавляем пустую строку перед нумерованными пунктами (кроме первого)
    text = re.sub(r'(?<!\n\n)\n(\d+\.\s+<b>)', r'\n\n\1', text)

    # Добавляем пустую строку перед <u>Обоснование:</u>, <u>Подтверждение:</u>, <u>Вывод:</u>
    text = re.sub(
        r'(?<!\n\n)(<u>(?:Обоснование|Подтверждение|Вывод):</u>)', r'\n\n\1', text)

    # Добавляем пустую строку перед буллет-листами (когда они идут после обычного текста)
    text = re.sub(r'([^•\n])\n(•\s+)', r'\1\n\n\2', text)

    # Нормализуем множественные переносы строк (больше 2 подряд -> 2)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Добавляем красивое оформление категории и пустую строку после разделителя
    text = re.sub(
        r'Категория = ([^\n]+)', r'Категория: \1\n━━━━━━━━━━━━━━━━━━━━━━━━\n', text)

    # Специальное форматирование для PCR тестов
    if 'pcr_test_interpretation' in text:
        # Заменяем • З на • 🟢 (зелёный кружок для положительных результатов)
        text = re.sub(r'• З([^\n]*)', r'• 🟢\1', text)
        # Заменяем • К на • 🔴 (красный кружок для контрольных/отрицательных результатов)
        text = re.sub(r'• К([^\n]*)', r'• 🔴\1', text)

    # Улучшаем отображение Ct значений: убираем пробелы вокруг '=', меняем десятичную точку на запятую
    text = re.sub(r'Ct\s*=\s*', 'Ct=', text)
    text = re.sub(r'Ct=(\d+)\.(\d+)', r'Ct=\1,\2', text)

    # Добавляем пустую строку перед предупреждением
    text = re.sub(r'([^\n])\n(⚠️ ВАЖНО:)', r'\1\n\n\2', text)

    # Убираем все оставшиеся HTML теги, которые не поддерживаются Telegram
    # Поддерживаются только: <b>, <strong>, <i>, <em>, <u>, <ins>, <s>, <strike>, <del>, <code>, <pre>, <a href="...">
    text = re.sub(
        r'</?(?!(b|strong|i|em|u|ins|s|strike|del|code|pre|a\s+href=|a>))[^>]+>', '', text)

    return text.strip()


def balance_html_tags(text: str) -> str:
    """
    Балансирует HTML теги в тексте для предотвращения ошибок парсинга в Telegram.
    Оптимизирован для работы с отдельными фрагментами сообщений.
    """
    if not text:
        return ""
    
    import re
    
    # Поддерживаемые теги
    supported_tags = {'b', 'strong', 'i', 'em', 'u', 'ins', 's', 'strike', 'del', 'code', 'pre'}
    
    # Быстрая проверка - если нет тегов, возвращаем как есть
    if not re.search(r'</?[a-zA-Z]', text):
        return text
    
    # Стек для отслеживания открытых тегов
    stack = []
    result_parts = []
    last_pos = 0
    
    # Регулярное выражение для поиска тегов
    tag_pattern = re.compile(r'</?([a-zA-Z]+)(?:\s+[^>]*)?>')
    
    # Обрабатываем все теги в тексте
    for match in tag_pattern.finditer(text):
        tag_full = match.group(0)
        tag_name = match.group(1).lower()
        tag_start, tag_end = match.span()
        
        # Добавляем текст до тега
        result_parts.append(text[last_pos:tag_start])
        last_pos = tag_end
        
        # Обрабатываем ссылки отдельно
        if tag_full.startswith('<a '):
            result_parts.append(tag_full)
            stack.append('a')
            continue
        elif tag_full == '</a>':
            if stack and stack[-1] == 'a':
                stack.pop()
                result_parts.append(tag_full)
            continue
        
        # Пропускаем неподдерживаемые теги
        if tag_name not in supported_tags:
            continue
        
        if tag_full.startswith('</'):
            # Закрывающий тег - ищем соответствующий открывающий в стеке
            if stack and stack[-1] == tag_name:
                stack.pop()
                result_parts.append(tag_full)
            # Иначе пропускаем непарный закрывающий тег
        else:
            # Открывающий тег
            result_parts.append(tag_full)
            stack.append(tag_name)
    
    # Добавляем оставшийся текст
    result_parts.append(text[last_pos:])
    
    # Закрываем все незакрытые теги в правильном порядке
    for tag in reversed(stack):
        result_parts.append(f'</{tag}>')
    
    balanced_text = ''.join(result_parts)
    
    # Убираем полностью пустые теги (без содержимого)
    balanced_text = re.sub(r'<(\w+)(?:\s+[^>]*)?>\s*</\1>', '', balanced_text)
    
    return balanced_text