import os
from app.utils.parsers.base_converter import BaseConverter
from app.utils.parsers.text_converters import TxtConverter, DocxConverter
from app.utils.parsers.table_converters import OdsConverter
from app.utils.parsers.image_converters import PdfConverter, ImageConverter
from typing import Optional


class ConverterFactory:
    """Фабрика для создания подходящего конвертера на основе расширения файла."""

    def __init__(self, file_path):
        """
        Инициализирует фабрику.

        :param file_path: Путь к файлу, который необходимо конвертировать.
        """
        self.file_path = file_path

    def convert(self) -> Optional[str]:
        """
        Производит конвертацию файла, используя соответствующий конвертер.

        :return: Результат конвертации в виде строки в случае успеха, None в случае ошибки.
        """
        converter = self.converter()
        if not converter:
            return None
        return converter.convert()

    def converter(self) -> BaseConverter:
        """
        Определяет и возвращает соответствующий класс конвертера в зависимости от расширения файла.

        :return: Экземпляр конвертера, соответствующий типу файла.
        :raises ValueError: Если тип файла не поддерживается.
        """
        file_extension = os.path.splitext(self.file_path)[1].lower()

        # конвертеры текста
        if file_extension == '.txt':
            return TxtConverter(self.file_path)
        elif file_extension in ('.doc', '.docx'):
            return DocxConverter(self.file_path)

        # конверторы таблиц
        elif file_extension == ".ods":
            return OdsConverter(self.file_path)

        # конверторы изображений и PDF-файлов
        elif file_extension == ".pdf":
            return PdfConverter(self.file_path)
        elif file_extension in ('.jpg', '.jpeg', '.png'):
            return ImageConverter(self.file_path)
        else:
            raise KeyError(f"Неподдерживаемый тип файла: {file_extension}")
