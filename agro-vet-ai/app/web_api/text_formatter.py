import re

def format_to_markdown(text: str) -> str:
    """
    Преобразует текст в Markdown формат.
    """
    if not text:
        return ""

    # Сначала обрабатываем некорректную разметку
    # Исправляем незакрытые теги (простой подход)
    text = re.sub(r'<b>(.*?)(?=<b>|</b>|$)', r'**\1**', text)
    text = re.sub(r'</b>', '', text)  # Удаляем оставшиеся закрывающие теги
    
    # Более надежная замена HTML тегов на Markdown
    text = re.sub(r'<strong\b[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<i\b[^>]*>(.*?)</i>', r'*\1*', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<em\b[^>]*>(.*?)</em>', r'*\1*', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Для подчеркивания
    text = re.sub(r'<u\b[^>]*>(.*?)</u>', r'*\1*', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<ins\b[^>]*>(.*?)</ins>', r'*\1*', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Зачеркивание
    text = re.sub(r'<s\b[^>]*>(.*?)</s>', r'~~\1~~', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<strike\b[^>]*>(.*?)</strike>', r'~~\1~~', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<del\b[^>]*>(.*?)</del>', r'~~\1~~', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Код
    text = re.sub(r'<code\b[^>]*>(.*?)</code>', r'`\1`', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<pre\b[^>]*>(.*?)</pre>', r'```\n\1\n```', text, flags=re.IGNORECASE | re.DOTALL)

    # Обрабатываем маркированные списки
    text = re.sub(r'•\s*(.*?)(?=\n|$)', r'- \1', text)
    
    # Обработка нумерованных списков
    lines = text.split('\n')
    processed_lines = []
    for line in lines:
        # Обработка нумерованных списков
        numbered_match = re.match(r'^(\d+)\.\s*(.*)', line.strip())
        if numbered_match:
            processed_lines.append(f"{numbered_match.group(1)}. {numbered_match.group(2)}")
        else:
            processed_lines.append(line)
    text = '\n'.join(processed_lines)

    # Заменяем <br> теги на переносы строк
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    
    # Заменяем <hr> теги на разделитель
    text = re.sub(r'<hr[^>]*>', '\n---\n', text, flags=re.IGNORECASE)
    
    # Заменяем теги <div> и <p> на переносы строк
    text = re.sub(r'</?(div|p)[^>]*>', '\n', text, flags=re.IGNORECASE)
    
    # Обработка ссылок
    text = re.sub(r'<a\s+[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Очищаем оставшиеся HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    
    # Нормализуем множественные переносы строк
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Убираем лишние пробелы в начале и конце
    text = text.strip()

    return text