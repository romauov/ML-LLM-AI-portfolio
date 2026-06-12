"""
Модуль обработки описания объявления кревтки.

@author Nikolay Zhabchikov
"""

import re
from nltk.stem.snowball import SnowballStemmer

from app.fishes.shrimp.data import shrimp_type, shrimp_type_mapping, sort_type, sort_type_mapping, frozen_type, \
    frozen_type_mapping, boxing_type, boxing_type_mapping, cutting_type, cutting_type_mapping, size_type, size_range, \
    size_type_mapping, shrimp_type_alias, cook_method_type, cook_method_type_mapping

stemmer = SnowballStemmer("russian")


def extract_data_from_description(text, types, types_alias_mapping=None):
    """
    Выделение информации из описания объявления.

    :param text: описание объявления.
    :param types: список с типами выделяемых объектов.
    :param types_alias_mapping: словарь с маппингом дубликатов.

    :return: str|None.
    """
    if not types_alias_mapping:
        types_alias_mapping = {}

    text = text.lower().strip()
    for type_ in types:
        if re.search(f'(^|\s|\(|/){type_}($|\s|\)|\.|,)', text):
            return types_alias_mapping.get(type_, type_)

    return None


def extract_shrimp_type(text, shrimp_types, shrimp_types_mapping):
    """
    Выделение типа креветки из описания объявления.

    :param text: описание объявления.
    :param shrimp_types: список с типами креветок.
    :param shrimp_types_mapping: словарь с маппингом дубликатов.

    :return: str|None.
    """
    text = text.lower().strip()
    stem_text = ' '.join([stemmer.stem(word) for word in text.split()])

    results = []
    for type_ in shrimp_types:
        stem_type = ' '.join([stemmer.stem(word) for word in type_.split()])
        # проверка вхождения подстроки в словах без учитывания подстроки в середине слова
        if re.search(f'(^|\s|,|\.|\\|\)|\(|-){stem_type}', stem_text):
            found_type = shrimp_types_mapping.get(type_, type_)
            results.append(found_type)

    n_unique = len(set(results))
    if n_unique > 1:
        if n_unique == 2 and 'лангустины' in results and 'лангуст' in results:
            return 'лангустины'
        return 'multiple values'
    elif n_unique == 1:
        return results[0]
    else:
        return None


def extract_shrimp_size(text, size_type, size_range, size_type_mapping):
    """
    Выделение размеров креветки.

    :param text: описание объявления.
    :param size_type: список с типами размеров креветок.
    :param size_range: список с размерами в виде диапазона.
    :param size_type_mapping: словарь с маппингом дубликатов.

    :return: List[str]|None.
    """
    text = text.lower().strip()
    for type_ in size_type:
        if re.search(f'(^|\s|\(){type_}($|\s|\)|\.|,)', text):
            return size_type_mapping.get(type_, type_)

    # ищем диапозон в формате 40/50, 40 50, 40-50
    for size_min, size_max in size_range:
        if re.search(f'{size_min}.{size_max}', text):
            return f'{size_min}/{size_max}'


def get_shrimp_alias(shrimp_type):
    """
    Возврат алиаса по переданному типу креветки.

    :param shrimp_type: тип креветки.

    :return: str|None.
    """
    return shrimp_type_alias.get(shrimp_type, None)


def get_shrimp_cuttings(text, cutting_type, cutting_type_mapping):
    """
    Выделение разрезов креветки.

    :param text: описание объявления.
    :param cutting_type: список с типами разрезов креветок.
    :param cutting_type_mapping: словарь с маппингом дубликатов.

    :return: List[str]|None.
    """
    text = text.lower().strip()
    cuttings = []
    for type_ in cutting_type:
        if re.search(f'(^|\s|\(){type_}($|\s|\)|\.|,)', text):
            cuttings.append(cutting_type_mapping.get(type_, type_))
    if cuttings:
        return str(cuttings).replace("'", "\"")

    return None


def get_shrimp_temperature_state(text, frozen_type, frozen_type_mapping):
    """
    Выделение заморозки креветки.

    :param text: описание объявления.
    :param frozen_type: список с типами заморозки креветок.
    :param frozen_type_mapping: словарь с маппингом дубликатов.

    :return: str|None.
    """
    text = text.lower().strip()
    for type_ in frozen_type:
        if re.search(f'(^|\s|\(){type_}($|\s|\)|\.|,)', text):
            # проверка на наличия отрицания
            if not re.search(f'без(^|\s|\(){type_}', text):
                return frozen_type_mapping.get(type_, type_)

    return None


def process_shrimp_dataframe_cols(df):
    """
    Обработка описания объявления креветки.

    :param df: dataframe с объявлениями.

    :return: dataframe.
    """
    df = df.copy()

    df['product_type'] = df['description'].apply(extract_shrimp_type, args=(shrimp_type, shrimp_type_mapping))
    df['product_type_alias'] = df['description'].apply(get_shrimp_alias)
    df['cutting'] = df['description'].apply(get_shrimp_cuttings, args=(cutting_type, cutting_type_mapping))
    df['sort'] = df['description'].apply(extract_data_from_description, args=(sort_type, sort_type_mapping))
    df['cook_method'] = df['description'].apply(
        extract_data_from_description,
        args=(cook_method_type, cook_method_type_mapping)
    )
    df['temperature_state'] = df['description'].apply(
        extract_data_from_description,
        args=(frozen_type, frozen_type_mapping)
    )
    df['boxing'] = df['description'].apply(extract_data_from_description, args=(boxing_type, boxing_type_mapping))
    df['size'] = df['description'].apply(extract_shrimp_size, args=(size_type, size_range, size_type_mapping))
    return df
