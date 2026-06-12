"""
Словарь для текста

@author Sergey Goncharov
"""
import io
import json


class TokenizerWord:
    """
    Словарь для текста
    """
    def __init__(self, words=None, path=None):
        self.word2index = {}
        self.index2word = {}

        if words is not None:
            self.add_text(words)

        if path is not None:
            self.open(path)

    def add_word(self, word: str):
        """
        Добавить слово в словарь
        """

        if word in self.word2index:
            return
        index = len(self.word2index)
        self.word2index[word] = index
        self.index2word[index] = word

    def add_text(self, text: str):
        """
        Добавить текст в словарь
        """
        for line in text:
            if not isinstance(line, str):
                line = '-'
            for word in line.split(' '):
                self.add_word(word)

    def get_index(self, word: str) -> int:
        """
        Получить индекс по слову
        """
        return self.word2index[word]

    def get_word(self, index: int) -> str:
        """
        Получить слово по индексу
        """
        return self.index2word[index]

    def tokens(self, text: str) -> list:
        """
        Замена слов на индексы в тексте
        """
        if not isinstance(text, str):
            text = '-'
        return [self.get_index(word) for word in text.split(' ')]

    def size(self):
        """
        Размер словаря
        """
        return len(self.word2index)

    def save(self, path: str):
        """
        Сохранить словарь в файл

        :param path: путь к файлу
        """
        obj = {'word2index': self.word2index, 'index2word': self.index2word}
        with io.open(path, 'w', encoding='utf-8') as file:
            file.write(json.dumps(obj))

    def open(self, path):
        """
        Загрузить словарь из файла

        :param path: путь к файлу
        """
        with open(path, encoding="utf-8") as json_file:
            data = json.load(json_file)
            self.word2index = data['word2index']
            self.index2word = {int(k): v for k, v in data['index2word'].items()}
