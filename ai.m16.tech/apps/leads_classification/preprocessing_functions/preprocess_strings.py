"""
Подготовка текста для модели с помощью re и natasha

@author Dmitry Avzalov, Yaroslav Koltashev
"""
import re

from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    Doc
)
from nltk.corpus import stopwords
import nltk

nltk.download('stopwords')


def clear_string(string, stop_words):  # Функция для очистки
    """
        Очищает строку от нежелательных символов и стоп-слов.

        Аргументы:
            string (str): Входная строка для очистки.
            stop_words (list): Список стоп-слов для удаления.

        Возвращает:
            str: Очищенная строка.
    """
    string = ' '.join([val for val in re.sub(r'[^а-яА-ЯёЁ\d]', ' ', str(string).lower()).split()
                       if not val in stop_words])
    return string


def natasha_lemmant(input_str, segmenter, morph_tagger, syntax_parser, morph_vocab):
    """
    Выполняет лемматизацию текста с использованием объектов `Segmenter`, `MorphTagger`, `SyntaxParser` и `MorphVocab`.

    Аргументы:
        input_str (str): Входная строка.
        segmenter (Segmenter): Объект Segmenter.
        morph_tagger (MorphTagger): Объект MorphTagger.
        syntax_parser (SyntaxParser): Объект SyntaxParser.
        morph_vocab (MorphVocab): Объект MorphVocab.

    Возвращает:
        str: Лемматизированная строка.

    """

    doc = Doc(input_str)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    doc.parse_syntax(syntax_parser)
    for token in doc.tokens:
        token.lemmatize(morph_vocab)

    result = ' '.join([_.lemma for _ in doc.tokens])
    return result


def preprocessing_data_for_predict(data):
    """
    Подготавливает данные для прогнозирования.

    Аргументы:
        data (list): Список данных для обработки.

    Возвращает:
        list: Список предобработанных данных.

    Эта функция принимает список данных и применяет несколько этапов предобработки, чтобы подготовить данные 
        для прогнозирования.
    Она инициализирует несколько объектов, таких как `Segmenter`, `MorphVocab`, `NewsEmbedding`,
        `NewsMorphTagger` и `NewsSyntaxParser`,
    которые используются в процессе предобработки.

    Затем функция перебирает каждый элемент входного списка данных и выполняет следующие шаги:
        - Вызывает функцию `clear_string` для удаления нежелательных символов и стоп-слов из текста.
        - Проверяет, что полученный текст не является пустым или состоит только из пробелов.
        - Вызывает функцию `natasha_lemmant` для выполнения лемматизации текста с использованием объектов `Segmenter`,
          `MorphTagger`, `SyntaxParser` и `MorphVocab`.
        - Добавляет предобработанный текст в список `result`.

    В конце функция возвращает список `result`, содержащий предобработанные данные.
    """
    segmenter = Segmenter()
    morph_vocab = MorphVocab()
    emb = NewsEmbedding()
    morph_tagger = NewsMorphTagger(emb)
    syntax_parser = NewsSyntaxParser(emb)

    stop_words = list(stopwords.words('russian'))

    result = []
    for example in data:
        text = clear_string(example, stop_words)
        if text not in ('', ' '):
            text = natasha_lemmant(text, segmenter, morph_tagger, syntax_parser, morph_vocab)
            result.append(text)

    return result
