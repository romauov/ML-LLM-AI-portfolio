import re

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter


class MDSplitter:
    """
    Сплиттер на чанки с разбиением на текст, таблицы, изображения
    """

    def __init__(self):
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False,
        )
        self.regex_rules_to_drop_string = [
            r'^\[\^0\]',
            'Table \d{1,3}\.\d{1,3}\. continued on next page'
        ]
        self.text_splitter = RecursiveCharacterTextSplitter(
            separators=[
                "\n\n",
                "\n",
                ". ",
                "? ",
                "! ",
            ],
            chunk_size=2000,
            is_separator_regex=False,
        )

    @staticmethod
    def fix_tables(content):
        content = content.replace('|\n|', '|to_replace|')

        # 2 раза, потому что регулярка пропускает через одну подходящие строки:
        # | Tiamulin \n Tiamulin | 1 \n 1 | 1 to \n 4 | 4 \n 5 |
        # при первом проходе проспустит | 1 \n 1 | и | 4 \n 5 |
        for _ in range(2):
            for match in re.findall(r'\|[^|]*\n[^|]*\|', content):

                if match != '\n':
                    match_new = match.replace('\n', ' ')
                    for table_head in re.findall(r'Table \d{1,3}\.\d{1,3}\.', match):
                        match = match.replace(table_head, f'\n\n{table_head}')

                    content = content.replace(match, match_new)

        content = content.replace('|to_replace|', '|\n|')
        return content

    def split_text_with_tables_and_figures(self, chunks):
        text_chunks, figure_chunks, table_chunks = [], [], []
        for split in chunks:
            content = split.page_content

            text, tables = [], []
            last_table_name = None
            is_table_parsing = False
            # построчно считываем каждый чанк
            for i in content.split('\n'):
                i_strip = i.strip()

                is_skip_string = False
                # "удаляем" строку, если она попадает под правило удаления
                for rule in self.regex_rules_to_drop_string:
                    if re.match(rule, i_strip):
                        is_skip_string = True
                        break

                if not is_skip_string:
                    # определение строки, как изображение
                    if figure_group := re.match(r'^Figure \d{1,3}\.\d{1,3}\.', i_strip):
                        figure_chunk = Document(
                            page_content=i,
                            metadata={'type': 'figure', 'name': figure_group.group()}
                        )
                        figure_chunks.append(figure_chunk)
                    # определение строки, как заголовка таблицы "Table 1.1. description"
                    elif table_group := re.match(r'^Table \d{1,3}\.\d{1,3}\.', i_strip):
                        if is_table_parsing:
                            table_chunk = Document(
                                page_content='\n'.join(tables),
                                metadata={'type': 'table', 'name': last_table_name}
                            )
                            table_chunks.append(table_chunk)
                            tables = []

                        is_table_parsing = True
                        last_table_name = table_group.group()
                        tables.append(i + '\n')
                    # определение строки, как строки таблицы
                    elif i_strip[0] == '|' and i_strip[-1] == '|':
                        is_table_parsing = True
                        tables.append(i)
                    # определение строки, как обычного текста
                    else:
                        if is_table_parsing:
                            is_table_parsing = False
                            table_chunk = Document(
                                page_content='\n'.join(tables),
                                metadata={'type': 'table', 'name': last_table_name}
                            )
                            table_chunks.append(table_chunk)
                            tables = []
                        text.append(i)
            # собираем обратно отдельные строки в чанк
            if tables:
                table_chunk = Document(
                    page_content='\n'.join(tables),
                    metadata={'type': 'table', 'name': last_table_name}
                )
                table_chunks.append(table_chunk)
            if text:
                text_chunk = Document(page_content='\n'.join(text), metadata={'type': 'text', **split.metadata})
                text_chunks.append(text_chunk)

        return text_chunks, figure_chunks, table_chunks

    def split_text_chunks(self, text_chunks):
        """
        Разбиение текстовых чанков по предложениям на более маленькие с вставкой в начало чанка
        markdown загловка (#, ##, ###).
        """
        handled_chunks = []
        for chunk in text_chunks:
            if chunk['metadata']['type'] != 'text':
                handled_chunks.append(chunk)
                continue

            rows = chunk['content'].split('\n')
            if all([row.startswith('#') for row in rows]):
                continue

            text_splits = self.text_splitter.split_text(chunk['content'])

            header = ''
            if header_3 := chunk['metadata'].get('Header 3'):
                header = f"### {header_3}\n{header}"
            if header_2 := chunk['metadata'].get('Header 2'):
                header = f"## {header_2}\n{header}"
            if header == '' and chunk['metadata'].get('Header 1'):
                header = f"# {chunk['metadata'].get('Header 1')}\n"

            text_documents = []
            for i, text_split in enumerate(text_splits):
                if i >= 1:
                    text_split = header + text_split
                text_documents.append({
                    'content': text_split,
                    'page_number': chunk['page_number'],
                    'chapter_title': chunk['chapter_title'],
                    'metadata': chunk['metadata']
                })

            handled_chunks.extend(text_documents)

        return handled_chunks

    def split(self, text):
        fixed_tables_text = self.fix_tables(text)
        chunks = self.splitter.split_text(fixed_tables_text)
        text_chunks, figure_chunks, table_chunks = self.split_text_with_tables_and_figures(chunks)
        return text_chunks, figure_chunks, table_chunks
