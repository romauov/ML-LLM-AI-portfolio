import re

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter


class BookSplitter:
    """
    Разбивает на чанки результаты парсинга utils/pdf-ocr-1.0 с учетом таблиц и изображений.

    - Функции с префиксом before_ модифицируют копию страниц pages, следует выполнять, ДО парсинга.
    - Функции с префиксом extract_ извлекают чанки в отдельные переменные.
    - Функции с префиксом after_ модифицируют извлеченные чанки, следует выполнять, ПОСЛЕ парсинга.

    Примеры использования:

    splitter = BookSplitter(
        pages=pages,                                # список страниц полученных через utils/pdf-ocr-1.0
        table_description_regex='Table \d{1,3} ',   # регулярное выражение для выделения заголовка таблиц
        image_description_regex='Figure \d{1,3} ',  # регулярное выражение для выделения описания изображения
        to_drop_line_regex='^\[\^0\]'               # регулярное выражение, исключающие текст
    )

    texts, tables, images = (splitter
                             .before_delete_newlines_symbol_at_table_cells()        # удаляем '\n' в ячейках таблицы
                             .extract_table()                                       # извлекаем таблицы
                             .extract_text()                                        # извлекаем текст
                             .extract_image()                                       # извлекаем изображения
                             .after_combine_single_table_separated_by_diff_pages()  # соединяем таблицы на разных стр.
                             .after_combine_single_text_separated_by_diff_pages()   # соединяем текст на разных стр.
                             .after_split_text_chunks()                             # разделяем большие текстовые чанки
                             .after_get_chunks())                                   # получаем списки с чанками

    Не обязательно использовать все функции, пример если не требуется выделять изображения,
    таблицы без переноса строк и таблицы полностью помещаются на странице:

    splitter = BookSplitter(
        pages=pages,
        table_description_regex='Table \d{1,3} ',
        image_description_regex='Figure \d{1,3} '
    )

    texts, tables, _ = (splitter
                        .extract_table()
                        .extract_text()
                        .after_combine_single_text_separated_by_diff_pages()
                        .after_split_text_chunks()
                        .after_get_chunks())

    При добавлении новой функции в парсер надо следовать правилам префиксов.
    Все функции меняют переменные экземпляра класса и возвращают self, кроме after_get_chunks.
    """

    def __init__(
            self,
            pages: list[dict],

            # регулярки
            image_description_regex: str = None,
            table_description_regex: str = None,
            to_drop_line_regex: str = None,

            # langchain сплиттеры
            markdown_headers_to_split_on: list[tuple[str, str]] = None,
            markdown_strip_headers: bool = False,
            text_separators: list[str] = None,
            text_chunk_size: int = 2000,

    ):
        """
        Args:
            pages: Список страниц полученных через utils/pdf-ocr-1.0 [{"index": 0, "markdown": "md text"}]
            image_description_regex: Регулярное выражение для выделения описания изображения. Обычно описание выглядит
                так 'Figure 1.1. Common enteric disease patterns in pigs', но при парсинге надо учитывать что название
                изображения может встречаться просто в тексте, как ссылка
                '\nEscherichia coli infections are ... high mortality (see Figure 1.1).\n'.
                Регулярное выражение должно находить строку с описанием, но не должно находить ссылку в середине
                текста. Пример подходящего выражения 'Figure \d{1,3}\.\d{1,3}\.'
            table_description_regex: Регулярное выражение для выделения описания таблицы. Как и с
                image_description_regex надо учитывать описание и ссылку на таблицу в тексте при составлении
                регулярного выражения
            to_drop_line_regex: Регулярное выражение, исключающие текст при парсинге
            markdown_headers_to_split_on: Headers we want to track
            markdown_strip_headers: Strip split headers from the content of the chunk
            text_separators: Список разделителей текста
            text_chunk_size: Maximum size of chunks to return
        """
        self.pages = pages
        self.image_description_regex = image_description_regex
        self.table_description_regex = table_description_regex
        self.to_drop_line_regex = to_drop_line_regex

        if not markdown_headers_to_split_on:
            markdown_headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ]
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=markdown_headers_to_split_on,
            strip_headers=markdown_strip_headers,
        )
        if not text_separators:
            text_separators = ["\n\n", "\n", ". ", "? ", "! ", ]
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=text_separators,
            chunk_size=text_chunk_size,
        )

        self.texts = []
        self.images = []
        self.tables = []

    def extract_text(self):
        """
        Выделяет из страниц текстовые чанки с разбиением по markdown заголовкам
        через langchain_text_splitters.MarkdownHeaderTextSplitter.
        Разбивает текст страницы по символу '\n' на части и считывает страницу последовательно.

        - Если задано регулярное выражение для изображений image_description_regex, то исключит описание изображения
        из текста, иначе добавит в текстовый чанк.
        - Если задано регулярное выражение для таблиц table_description_regex, то исключит таблицы из текста,
        иначе добавит в текстовый чанк.
        - Исключает текст попадающий под регулярные выражения to_drop_line_regex.
        """
        for page in self.pages:
            text_ = []
            content = page['markdown']
            for row in content.split('\n'):
                row_strip = row.strip()

                if (
                        not row_strip
                        or (self.to_drop_line_regex and re.match(self.to_drop_line_regex, row_strip))
                        or (self.image_description_regex and re.match(self.image_description_regex, row_strip))
                        or (self.table_description_regex and re.match(self.table_description_regex, row_strip))
                        or (self.table_description_regex and row_strip[0] == '|' and row_strip[-1] == '|')
                ):
                    continue

                text_.append(row)

            text_chunks = self.splitter.split_text('\n'.join(text_))
            for text_chunk in text_chunks:
                self.texts.append({
                    'type': 'text',
                    'content': text_chunk.page_content,
                    'page_number': page['index'] + 1,
                    'metadata': text_chunk.metadata
                })
        return self

    def extract_image(self):
        """
        Выделяет из страниц чанки описания изображений.
        Разбивает текст страницы по символу '\n' на части и считывает страницу последовательно.

        - Используется, только если задано регулярное выражение для изображений image_description_regex.
        - Исключает текст попадающий под регулярные выражения to_drop_line_regex.
        """
        if not self.image_description_regex:
            raise KeyError('Не задано регулярное выражения image_description_regex')

        for page in self.pages:
            content = page['markdown']
            for row in content.split('\n'):
                row_strip = row.strip()

                if not row_strip or (self.to_drop_line_regex and re.match(self.to_drop_line_regex, row_strip)):
                    continue

                if image_group := re.match(self.image_description_regex, row_strip):
                    self.images.append({
                        'type': 'figure',
                        'name': image_group.group(),
                        'content': row,
                        'page_number': page['index'] + 1
                    })

        return self

    def extract_table(self):
        """
        Выделяет из страниц чанки с таблицами.
        Разбивает текст страницы по символу '\n' на части и считывает страницу последовательно.

        - Используется, только если задано регулярное выражение для таблиц table_description_regex.
        - Исключает текст попадающий под регулярные выражения to_drop_line_regex.
        """

        if not self.table_description_regex:
            raise KeyError('Не задано регулярное выражения table_description_regex')

        for page in self.pages:
            content = page['markdown']
            tables_ = []
            is_table_parsing = False
            last_table_name = None
            for row in content.split('\n'):
                row_strip = row.strip()

                if not row_strip or (self.to_drop_line_regex and re.match(self.to_drop_line_regex, row_strip)):
                    continue

                if table_group := re.match(self.table_description_regex, row_strip):
                    if is_table_parsing:
                        self.tables.append({
                            'type': 'table',
                            'name': last_table_name,
                            'content': '\n'.join(tables_),
                            'page_number': page['index'] + 1
                        })
                        tables_ = []

                    is_table_parsing = True
                    last_table_name = table_group.group()
                    tables_.append(row)

                elif row_strip[0] == '|' and row_strip[-1] == '|':
                    is_table_parsing = True
                    tables_.append(row)
                else:
                    if tables_:
                        self.tables.append({
                            'type': 'table',
                            'name': last_table_name,
                            'content': '\n'.join(tables_),
                            'page_number': page['index'] + 1
                        })
                        is_table_parsing = False
                        last_table_name = None
                        tables_ = []

            if tables_:
                self.tables.append({
                    'type': 'table',
                    'name': last_table_name,
                    'content': '\n'.join(tables_),
                    'page_number': page['index'] + 1
                })

        return self

    def before_delete_newlines_symbol_at_table_cells(self):
        """Удаляет символ переноса строки внутри ячейки таблицы."""

        if not self.table_description_regex:
            raise KeyError('Необходимо задать регулярное выражение для выделения названия таблицы')

        for i, page in enumerate(self.pages):
            content = page['markdown']
            content = content.replace('|\n|', '|table_new_line|')

            # 2 раза, потому что регулярка пропускает через одну подходящие строки:
            # | 1 \n 1 | 2 \n 2 | 3 \n 3 | 4 \n 4 |
            # при первом проходе проспустит | 2 \n 2 | и | 4 \n 4 |
            for _ in range(2):
                for match in re.findall(r'\|[^|]*\n[^|]*\|', content):

                    if match != '\n':
                        match_new = match.replace('\n', ' ')
                        for table_head in re.findall(self.table_description_regex, match_new):
                            match_new = match.replace(table_head, f'\n\n{table_head}')

                        content = content.replace(match, match_new)

            content = content.replace('|table_new_line|', '|\n|')
            page['markdown'] = content

        return self

    def after_combine_single_text_separated_by_diff_pages(self, combiner_sign='\n'):
        """
        Соединяет текстовые чанки разделенные разными страницами в один чанк.

        Args:
            combiner_sign: Символ соединения чанков.
        """
        texts_ = []

        for text in self.texts:
            if len(text['metadata']) == 0 and len(texts_) > 0:
                last_text = texts_.pop(-1)
                last_text['content'] = f'{last_text["content"]}{combiner_sign}{text["content"]}'
                texts_.append(last_text)
            else:
                texts_.append(text)

        self.texts = texts_
        return self

    def after_combine_single_table_separated_by_diff_pages(self, combiner_sign='\n'):
        """
        Соединяет чанки с таблицами разделенные разными страницами в один чанк.

        Args:
            combiner_sign: Символ соединения чанков.
        """
        tables_ = []

        for table in self.tables:
            if not table.get('name') and len(tables_):
                last_table = tables_.pop(-1)
                last_table['content'] = f'{last_table["content"]}{combiner_sign}{table["content"]}'
                tables_.append(last_table)
            else:
                tables_.append(table)

        self.tables = tables_
        return self

    def after_split_text_chunks(self):
        """
        Разделяет тектсовые чанки с сохранением заголовка чанка на более маленькие через
        langchain_text_splitters.RecursiveCharacterTextSplitter.
        """
        texts_ = []

        for text in self.texts:
            if all([row.strip().startswith('#') for row in text['content'].split('\n')]):
                continue

            header = ''
            if header_1 := text['metadata'].get('Header 1'):
                header = f'{header}\n# {header_1}'
            if header_2 := text['metadata'].get('Header 2'):
                header = f'{header}\n## {header_2}'
            if header_3 := text['metadata'].get('Header 3'):
                header = f'{header}\n### {header_3}'
            header = header.strip()

            text_splits = self.text_splitter.split_text(text['content'])

            text_chunks = []
            for i, text_split in enumerate(text_splits):
                if i >= 1:
                    text_split = f'{header}\n{text_split}'
                text_chunks.append({
                    'type': text['type'],
                    'content': text_split,
                    'page_number': text['page_number'],
                    'metadata': text['metadata']
                })

            texts_.extend(text_chunks)

        self.texts = texts_
        return self

    def after_get_chunks(self):
        return self.texts, self.tables, self.images
