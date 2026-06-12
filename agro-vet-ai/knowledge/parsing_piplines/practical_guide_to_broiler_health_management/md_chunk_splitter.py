import re

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter


class MDSplitter:
    """
    Сплиттер на чанки с разбиением на текст, таблицы, изображения для книги Dr Imre Horváth-Papp
    """

    def __init__(self, text):
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False
        )
        self._splits = self.md_splitter.split_text(text)
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=[
                "\n\n",
                "\n",
                ". ",
                "? ",
                "! ",
            ],
            chunk_size=3000,
            # chunk_overlap=250,
            is_separator_regex=False,
        )
        self.figure_re = r"\!\[img-\d+\.jpeg\]\(img-\d+\.jpeg\)"

    def split_text_with_tables_and_figures(self):
        """
        Разбиение markdown текста на чанки по заговкам (#, ##, ###) с выделением в отдельные чанки изображений
        с их описанием и таблиц.
        """
        text_chunks, figure_chunks, table_chunks = [], [], []
        for split in self._splits:
            content = split.page_content
            text, tables, figures = [], [], []
            is_table_parsing = False
            is_figure_parsing = False
            is_need_concatenate = False

            # построчно считываем каждый чанк
            for row in content.split('\n'):
                i_strip = row.strip()

                # определение строки, как изображения
                if re.match(self.figure_re, i_strip):
                    is_figure_parsing = True

                # определение строки, как таблицы
                elif i_strip[0] == '|' and i_strip[-1] == '|':
                    tables.append(row)
                    is_table_parsing = True

                # определение строки, как обычный текст
                else:
                    # если предыдущая строка была таблицей, то считаем что таблица закончилась и формируем документ
                    if is_table_parsing:
                        table_chunk = Document(
                            page_content='\n'.join(tables),
                            metadata={'type': 'table'}
                        )
                        table_chunks.append(table_chunk)
                        tables = []
                        is_need_concatenate = True
                        is_table_parsing = False

                    # если предыдущая строка была изображением, то считаем что следующие 2 строки это ее описание
                    if is_figure_parsing:
                        figures.append(row)
                        if len(figures) >= 2:
                            figure_chunk = Document(
                                page_content='\n'.join(figures),
                                metadata={'type': 'figure', 'name': figures[0]}
                            )
                            figure_chunks.append(figure_chunk)
                            figures = []
                            is_figure_parsing = False
                            is_need_concatenate = True

                    else:
                        if is_need_concatenate:
                            row = f"{text.pop(-1)} {row}"
                            is_need_concatenate = False

                        if row.startswith('#'):
                            row = row.upper()

                        text.append(row)

            # собираем обратно отдельные строки в чанк
            if tables:
                table_chunk = Document(
                    page_content='\n'.join(tables),
                    metadata={'type': 'table'}
                )
                table_chunks.append(table_chunk)
            if text:
                metadata = {
                    key: value.upper() if isinstance(value, str) else value
                    for key, value in split.metadata.items()
                }
                metadata.update({'type': 'text'})

                text_chunk = Document(page_content='\n'.join(text), metadata=metadata)
                text_chunks.append(text_chunk)

        return text_chunks, figure_chunks, table_chunks

    def split_text_chunks(self, text_chunks):
        """
        Разбиение текстовых чанков по предложениям на более маленькие с вставкой в начало чанка
        markdown загловка (#, ##, ###).
        """
        handled_text_chunks = []
        for chunk in text_chunks:

            rows = chunk.page_content.split('\n')
            if all([row.startswith('#') for row in rows]):
                print('Обнаружен чанк только с заголовками, пропускаем чанк')
                continue

            text_splits = self.text_splitter.split_text(chunk.page_content)

            header = ''
            if header_3 := chunk.metadata.get('Header 3'):
                header = f"### {header_3}\n{header}"
            if header_2 := chunk.metadata.get('Header 2'):
                header = f"## {header_2}\n{header}"
            if header == '' and chunk.metadata.get('Header 1'):
                header = f"# {chunk.metadata.get('Header 1')}\n"

            text_documents = []
            for i, text_split in enumerate(text_splits):
                if i >= 1:
                    text_split = header + text_split
                text_documents.append(Document(page_content=text_split, metadata=chunk.metadata))

            handled_text_chunks.extend(text_documents)

        return handled_text_chunks

    def split(self):
        text_chunks, figure_chunks, table_chunks = self.split_text_with_tables_and_figures()
        text_chunks = self.split_text_chunks(text_chunks)
        return text_chunks, figure_chunks, table_chunks
