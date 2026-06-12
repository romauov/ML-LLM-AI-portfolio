def preprocess_remove_text_between_h1_and_h2(pages):
    """
    Удаляет текст между Header 1 (# ) и Header 2 (## ).
    Также удаляет секции References (## References, ## 9 References, ## 16ii. 11 References и т.д.).
    Это нужно для удаления информации об авторах и аффилиациях,
    которые попадают в бесполезные чанки.
    """
    processed_pages = []

    for page in pages:
        lines = page['markdown'].split('\n')
        filtered_lines = []
        skip_mode = False
        skip_references = False

        for line in lines:
            stripped = line.strip()

            # Если встречаем Header 1 - начинаем пропускать следующий текст до следующего H2/H3
            if stripped.startswith('# ') and not stripped.startswith('## '):
                filtered_lines.append(line)
                skip_mode = True
                skip_references = False
                continue

            # Если встречаем заголовок References (любого уровня 2-3)
            if (stripped.startswith('## ') or stripped.startswith('### ')) and 'References' in stripped:
                skip_references = True
                skip_mode = False
                continue

            # Если встречаем обычный Header 2 или Header 3 - прекращаем все режимы пропуска
            if stripped.startswith('## ') or stripped.startswith('### '):
                skip_mode = False
                skip_references = False
                filtered_lines.append(line)
                continue

            # Если в режиме пропуска - пропускаем
            if skip_mode or skip_references:
                continue

            # Добавляем строку
            filtered_lines.append(line)

        processed_pages.append({
            **page,
            'markdown': '\n'.join(filtered_lines)
        })

    return processed_pages