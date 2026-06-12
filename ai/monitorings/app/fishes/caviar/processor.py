"""
Модуль обработки описания объявления икры.

@author Nikolay Zhabchikov
"""

import re
import datetime
from nltk.stem.snowball import SnowballStemmer

from app.fishes.caviar.data import color_type, color_mapping, boxing_type, \
    boxing_mapping, cook_method_type, cook_method_mapping, frozen_type, frozen_mapping, \
    product_class, product_class_mapping, salt_types, salt_mapping, sort_mapping, sort_types, \
    caviar_types, caviar_types_mapping, caviar_type_alias, cook_method_negative_particles

stemmer = SnowballStemmer("russian")


def extract_caviar_period_type(text):
    """
    Выделение периода икры из описания объявления.

    :param text: описание объявления.

    :return: str|None.
    """
    text = text.lower().strip()

    period_type = range(2008, datetime.date.today().year + 1)
    for period in period_type:
        if re.search(f'(^|\s|\()путина {str(period)}', text):
            return str(period)

    return None


def extract_data_from_description(text, types, types_mapping=None, negative_particles=None):
    """
    Выделение информации из описания объявления.

    :param text: описание объявления.
    :param types: список с типами выделяемых объектов.
    :param types_mapping: словарь с маппингом дубликатов.
    :param negative_particles: список с отрицательными чатицми речи.

    :return: str|None.
    """
    if not types_mapping:
        types_mapping = {}

    text = text.lower().strip()
    for type_ in types:
        if re.search(f'(^|\s|\(){type_}($|\s|\)|\.|,)', text):
            if negative_particles:
                negative_expression = '|'.join(negative_particles)
                if not re.search(f'({negative_expression})(^|\s|\(){type_}', text):
                    return types_mapping.get(type_, type_)
            else:
                return types_mapping.get(type_, type_)

    return None


def extract_caviar_type(text, caviar_types, caviar_types_mapping):
    """
    Выделение типа икры из описания объявления.

    :param text: описание объявления.
    :param caviar_types: список с типами икры.
    :param caviar_types_mapping: словарь с маппингом дубликатов.

    :return: str|None.
    """
    text = text.lower().strip()
    stem_text = ' '.join([stemmer.stem(word) for word in text.split()])

    results = []
    for type_ in caviar_types:
        stem_type = stemmer.stem(type_)
        # проверка вхождения подстроки в словах без учитывания подстроки в середине слова
        if re.search(f'(^|\s|,|\.|\\|\)|\(|-){stem_type}', stem_text):
            found_type = caviar_types_mapping.get(type_, type_)
            results.append(found_type)

    n_unique = len(set(results))
    if n_unique > 1:
        if n_unique == 2:
            # обработка добавления в описание "лососевая" вместе с другим типом
            salmon = caviar_types_mapping.get('лососевая')
            if salmon in results and 'лосос' in text:
                for product_type in results:
                    if product_type != salmon:
                        return product_type
            # обработка масаго из сельди
            if 'масаго' in results and 'сельдь' in results:
                return 'масаго'
            # обработка стреляди при указании что семейство осетровое
            if 'стерлядь' in results and 'осетр' in results:
                return 'стерлядь'
        return 'multiple values'
    elif n_unique == 1:
        return results[0]
    else:
        return None


def get_caviar_alias(caviar_type):
    """
    Возврат алиаса по переданному типу икры.

    :param caviar_type: тип икры.

    :return: str|None.
    """
    return caviar_type_alias.get(caviar_type, None)


def process_caviar_dataframe_cols(df):
    """
    Обработка описания объявления икры.

    :param df: dataframe с объявлениями.

    :return: dataframe.
    """
    df = df.copy()
    df['product_type'] = df['description'].apply(extract_caviar_type, args=(caviar_types, caviar_types_mapping))
    df['product_type_alias'] = df['product_type'].apply(get_caviar_alias)
    df['sort'] = df['description'].apply(extract_data_from_description, args=(sort_types, sort_mapping))
    df['salt'] = df['description'].apply(extract_data_from_description, args=(salt_types, salt_mapping))
    df['product_class'] = df['description'].apply(
        extract_data_from_description,
        args=(product_class, product_class_mapping)
    )
    df['temperature_state'] = df['description'].apply(
        extract_data_from_description,
        args=(frozen_type, frozen_mapping)
    )
    df['cook_method'] = df['description'].apply(
        extract_data_from_description,
        args=(cook_method_type, cook_method_mapping, cook_method_negative_particles)
    )
    df['boxing'] = df['description'].apply(extract_data_from_description, args=(boxing_type, boxing_mapping))
    df['color'] = df['description'].apply(extract_data_from_description, args=(color_type, color_mapping))
    df['period'] = df['description'].apply(extract_caviar_period_type)
    return df
