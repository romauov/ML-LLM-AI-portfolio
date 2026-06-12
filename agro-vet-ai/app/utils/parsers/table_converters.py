import pandas as pd
from app.utils.parsers.base_converter import BaseConverter
from typing import Optional


class OdsConverter(BaseConverter):
    """Конвертер ODS-файлов. Преобразует содержимое в CSV-строку."""

    def convert(self) -> Optional[str]:
        """
        Конвертирует ODS-файл в CSV-строку.

        :return: Данные в формате CSV или None.
        """
        df = pd.read_excel(self.file_path, engine='odf')

        csv_string = df.to_csv(index=False, sep=";")
        if csv_string is not None:
            csv_string = csv_string.strip()

        return csv_string
