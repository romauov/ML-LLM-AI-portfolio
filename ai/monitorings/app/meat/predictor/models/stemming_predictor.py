"""
Скрипт для предсказания с помощью алгоритмов проверки вхождения названия категории в описании.

@author Nikolay Zhabchikov
"""
import os

import pandas as pd
import re
from nltk.stem.snowball import SnowballStemmer

from app.meat.utils.data import categories_mapping

stemmer = SnowballStemmer("russian")

negative_parts_regex = '(?:^|\s|\(|,)(?:без|на|с)(?:$|\s|\)|\.|,)'
possible_negative_parts_categories = ['кожа', 'кость', 'жир', 'костный остаток', 'шкура', 'баки', 'Кишки', 'Сало',
                                      'жилка', 'кишка', 'хрящи', 'кости']


def sentence_stemming_for_mutton(text):
    """
    Преобразование слов в стеммы и удаление лишних символов.
    отдельная функция для баранины, не удаляются числа 12 и 6 которые содержаться в названии категорий
    Args:
        text: текстовое описание

    Returns:
        str: строка стостоящая из стемм слов текста
    """
    text = re.sub('[^а-яА-Я0-9]+', ' ', text)
    text = text.lower().strip()

    to_join = []
    for word in text.split():
        if word in ['12', '6']:
            to_join.append(word)
        elif len(word) > 2:
            to_join.append(stemmer.stem(word))

    text = ' '.join(to_join)
    return text


def sentence_stemming(text):
    """
    Преобразование слов в стеммы и удаление лишних символов
    Args:
        text: текстовое описание

    Returns:
        str: строка стостоящая из стемм слов текста
    """
    text = re.sub('[^а-яА-Я]+', ' ', text)
    text = text.lower().strip()
    text = ' '.join([stemmer.stem(word) for word in text.split() if len(word) > 2])
    return text


def stemming_predict_class(text, class_names_stemming, stemming_to_class):
    """
    Предсказание класса
    Args:
        text: текстовое описание
        class_names_stemming: стеммы возможных классов
        stemming_to_class: маппинг стемм к обычному названию классов

    Returns:
        str|None: Название класса, если обнаружено вхождение только одного названия класса, иначе None
    """
    candidate = None
    for name in class_names_stemming:
        # если название категории это одно слово, то ищем по словам в списке, иначе ищем по подстроке
        text_ = text.split() if len(name.split()) == 1 else text
        if name in text_:
            if not candidate:
                candidate = name
            elif name not in candidate:
                return None
    if candidate:
        return stemming_to_class[candidate]
    return None


def predict_on_stemming(df):
    """
    Предсказание product_type с помощью алгоритмов проверки вхождения названия категории в описании.
    Используется стемма описания и категории при проверке вхождения
    Args:
        df (DataFrame): датафрейм мониторинга

    Returns:
        DataFrame: датафрейм мониторинга с предсказаниями
    """
    to_preds_df = df[df['product_type'].isna()]

    for category in categories_mapping.keys():
        path_to_categories = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data', 'categories', f'{category}_разрубы.csv'
        )
        class_names = list(pd.read_csv(path_to_categories, sep=';')['value'].unique())
        sub_df = to_preds_df[to_preds_df['product'].isin(categories_mapping[category])].copy()

        if category == 'Баранина':
            class_names = class_names[1:]
            class_names_stem = [sentence_stemming_for_mutton(i) for i in class_names]
            sub_df['description_stemming'] = sub_df['description'].apply(sentence_stemming_for_mutton)
        else:
            class_names_stem = [sentence_stemming(i) for i in class_names]
            sub_df['description_stemming'] = sub_df['description'].apply(sentence_stemming)

        stem_to_class = {class_names_stem[i]: class_names[i] for i in range(len(class_names))}
        class_names_stem = sorted(class_names_stem, key=len, reverse=True)
        sub_df['product_type'] = [stemming_predict_class(text, class_names_stem, stem_to_class) for text in
                                  sub_df['description_stemming']]

        # удаляем предсказания классов которые могуть быть с отрицанием
        to_drop = sub_df[
            ((sub_df['product_type'].isin(possible_negative_parts_categories))
             & (sub_df['description'].str.contains(negative_parts_regex, regex=True)))
            ]
        sub_df = sub_df.drop(to_drop.index, axis=0)
        to_preds_df.loc[sub_df.index, 'product_type'] = sub_df['product_type']

        # Замена категории "Фарш", если в описани присутсвует "мех"
        if category == 'Птица':
            replace_cat = 'мясо механической обвалки'
        else:
            replace_cat = 'мясо'
        to_replace = sub_df[(sub_df['product_type'] == 'фарш') & (sub_df['description'].str.contains('мех'))]
        to_preds_df.loc[to_replace.index, 'product_type'] = replace_cat

    df.loc[to_preds_df.index, 'product_type'] = to_preds_df['product_type']
    return df
