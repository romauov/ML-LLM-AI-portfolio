import re

def remove_markdown(text):
    """
    Удаляет Markdown-разметку из текста, включая:
    - Блоки кода (многострочные и инлайновые)
    - Изображения и ссылки
    - Жирное и курсивное форматирование
    - Заголовки, списки, цитаты
    - Горизонтальные разделители
    - HTML-комментарии
    - Экранированные символы
    - Специфичные LLM-шаблоны (например, ```json)
    
    Сохраняет текстовое содержимое элементов (например, текст ссылок).
    """
    # Удаление блоков кода (сохраняем содержимое)
    text = re.sub(r'```[^\n]*\n(.*?)```', r'\1', text, flags=re.DOTALL)
    
    # Удаление инлайнового кода
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Удаление изображений (сохраняем alt-текст)
    text = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', text)
    
    # Замена ссылок на текстовое описание
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Удаление жирного и курсивного форматирования
    for _ in range(2):  # Двух проходов достаточно для вложенных форматов
        text = re.sub(r'\*\*(\*?[^*]+\*?)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Удаление заголовков
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[=-]{2,}\s*$', '', text, flags=re.MULTILINE)
    
    # Удаление маркеров списков и цитат
    text = re.sub(r'^[\s]*[-*+]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    
    # Удаление горизонтальных линий
    text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    
    # Удаление HTML-комментариев
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # Обработка экранированных символов
    text = re.sub(r'\\([\\`*{}\[\]()#+\-.!_~|<>])', r'\1', text)
    
    # Удаление специфичных LLM-шаблонов (например, ```json)
    text = re.sub(r'^```[a-z]*\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Очистка пустых строк и лишних пробелов
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n'.join(lines)