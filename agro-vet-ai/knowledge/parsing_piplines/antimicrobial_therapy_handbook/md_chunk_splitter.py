import re

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter


class MDSplitter:
    """
    Сплиттер на чанки с разбиением на текст, таблицы, изображения
    """

    def __init__(self, text):
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False
        )
        self._splits = self.splitter.split_text(text)
        self.regex_rules_to_drop_string = [r'^\[\^0\]']

    def split_text_with_tables_and_figures(self):
        text_chunks, figure_chunks, table_chunks = [], [], []
        for split in self._splits:
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
                        is_table_parsing = True
                        last_table_name = table_group.group()
                        tables.append(i + '\n')
                    # определение строки, как строки таблицы
                    elif i_strip[0] == '|' and i_strip[-1] == '|':
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
                text_chunk = Document(page_content='\n'.join(text), metadata=split.metadata)
                text_chunks.append(text_chunk)

        return text_chunks, figure_chunks, table_chunks
