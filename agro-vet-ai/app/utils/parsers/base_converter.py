from typing import Optional
from abc import ABC, abstractmethod


class BaseConverter(ABC):
    """
    Базовый класс для всех конвертеров.
    Определяет интерфейс для конвертации различных форматов файлов.
    """

    def __init__(self, file_path):
        """
        Инициализирует конвертер.

        :param file_path: Путь к файлу, который требуется конвертировать.
        """
        self.file_path = file_path

    @abstractmethod
    def convert(self) -> Optional[str]:
        """
        Абстрактный метод конвертации файла.

        :return: Преобразованное содержимое файла в виде строки в случае успеха, None в случае ошибки.
        """
        pass
