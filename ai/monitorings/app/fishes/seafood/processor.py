"""
Модуль с данными для обработки объявлений морепродуктов.

@author Nikolay Zhabchikov
"""

import re
from nltk.stem.snowball import SnowballStemmer

from app.fishes.seafood.data import seafood_type_alias, seafood_type, seafood_type_mapping, sort_type, \
    sort_type_mapping, goods_type, goods_type_mapping, frozen_type, frozen_type_mapping, boxing_type, \
    boxing_type_mapping, size_type, size_type_mapping, cook_method_type, cook_method_type_mapping, cutting_type, \
    cutting_type_mapping, whole_word_seafood_types, whole_word_goods_types

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


def extract_permutation_stemming_data_from_description(text, types, types_alias_mapping, whole_word_types=None):
    """
    Выделение информации из описания объявления с использованием стемминга и перестановки слов местами.

    :param text: описание объявления.
    :param types: список с типами выделяемых объектов.
    :param types_alias_mapping: словарь с маппингом дубликатов.
    :param whole_word_types: список с типами для которых осуществляется поиск без вхождения в слово.

    :return: str|None.
    """
    text = text.lower().strip()
    stem_text = ' '.join([stemmer.stem(word) for word in text.split()])

    results = []
    for type_ in types:
        found_words = []
        words = type_.split()
        # проверка наличия каждого слова из типа в описании, для обработки перестановок (краб стригун, стригун краб)
        for word in words:
            stem_type = stemmer.stem(word)

            if whole_word_types and type_ in whole_word_types:
                # проверка вхождения отдельного слова в тексте
                regular_exp = f'(^|\s|,|\.|\\|\)|\(|-){stem_type}($|\s|\)|\.|,)'
            else:
                # проверка вхождения подстроки в словах без учитывания подстроки в середине слова
                regular_exp = f'(^|\s|,|\.|\\|\)|\(|-){stem_type}'
            if re.search(regular_exp, stem_text):
                found_words.append(word)
        if found_words == words:
            found_type = types_alias_mapping.get(type_, type_)
            results.append(found_type)

    return results


def extract_seafood_type(text, seafood_type, seafood_type_mapping, whole_word_types):
    """
    Выделение типа морепродукта из описания объявления.

    :param text: описание объявления.
    :param goods_type: список с типами морепродуктов.
    :param goods_type_mapping: словарь с маппингом дубликатов.
    :param whole_word_types: список с типами для которых осуществляется поиск без вхождения в слово.

    :return: str|None.
    """
    results = extract_permutation_stemming_data_from_description(
        text, seafood_type, seafood_type_mapping, whole_word_types
    )
    results = list(set(results))
    n_unique = len(results)

    if n_unique > 1:
        if n_unique == 2:
            if results[0] in results[1]:
                return results[1]
            if results[1] in results[0]:
                return results[0]
        return 'multiple values'
    elif n_unique == 1:
        return results[0]
    else:
        return None


def extract_seafood_goods_type(text, goods_type, goods_type_mapping, whole_word_types):
    """
    Выделение типа товара морепродуктов из описания объявления.

    :param text: описание объявления.
    :param goods_type: список с типами товаров.
    :param goods_type_mapping: словарь с маппингом дубликатов.
    :param whole_word_types: список с типами для которых осуществляется поиск без вхождения в слово.

    :return: str|None.
    """
    results = extract_permutation_stemming_data_from_description(text, goods_type, goods_type_mapping, whole_word_types)
    results = list(set(results))

    if 'щупальца' in results and 'с щупальцами' in text:
        results.remove('щупальца')

    n_unique = len(results)
    if n_unique > 1:
        if n_unique == 2:
            if 'филе' in results and 'из филе' in text:
                results.remove('филе')
                return results[0]
            if 'роза' in results and 'без роз' in text:
                results.remove('роза')
                return results[0]
            if 'кольца' in results and 'колено' in results:
                return 'кольца'
            if results[0] in results[1]:
                return results[1]
            if results[1] in results[0]:
                return results[0]
        if n_unique == 3 and 'мясо' in results and 'колено' in results and 'мясо коленца' in results:
            return 'мясо коленца'
        return 'multiple values'
    elif n_unique == 1:
        return results[0]
    else:
        return None


def get_seafood_alias(seafood_type):
    """
    Возврат алиаса по переданному типу морепродуктов.

    :param seafood_type: тип морепродуктов.

    :return: str|None.
    """
    return seafood_type_alias.get(seafood_type, None)


def get_seafood_cuttings(text, cutting_type, cutting_type_mapping):
    """
    Выделение разрезов морепродуктов.

    :param text: описание объявления.
    :param cutting_type: список с типами разрезов морепродуктов.
    :param cutting_type_mapping: словарь с маппингом дубликатов.

    :return: List[str]|None.
    """
    text = text.lower().strip()
    stem_text = ' '.join([stemmer.stem(word) for word in text.split()])

    cuttings = []

    for type_ in cutting_type:
        stem_type = ' '.join([stemmer.stem(word) for word in type_.split()])
        if re.search(f'(^|\s|\(){stem_type}($|\s|\)|\.|,)', stem_text):
            # проверка на наличие отрицания
            if not re.search(f'без(^|\s|\(){stem_type}', stem_text):
                cuttings.append(cutting_type_mapping.get(type_, type_))
    if cuttings:
        return str(list(set(cuttings))).replace("'", "\"")

    return None


def get_seafood_temperature_state(text, frozen_type, frozen_type_mapping):
    """
    Выделение заморозки морепродуктов.

    :param text: описание объявления.
    :param frozen_type: список с типами заморозки морепродуктов.
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


def process_seafood_dataframe_cols(df):
    """
    Обработка описания объявления морепродуктов.

    :param df: dataframe с объявлениями.

    :return: dataframe.
    """
    df = df.copy()
    df['product_type'] = df['description'].apply(
        extract_seafood_type,
        args=(seafood_type, seafood_type_mapping, whole_word_seafood_types)
    )
    df['product_type_alias'] = df['product_type'].apply(get_seafood_alias)
    df['sort'] = df['description'].apply(extract_data_from_description, args=(sort_type, sort_type_mapping))
    df['goods_type'] = df['description'].apply(extract_seafood_goods_type,
                                               args=(goods_type, goods_type_mapping, whole_word_goods_types))
    df['cutting'] = df['description'].apply(get_seafood_cuttings, args=(cutting_type, cutting_type_mapping))
    df['temperature_state'] = df['description'].apply(
        get_seafood_temperature_state,
        args=(frozen_type, frozen_type_mapping)
    )
    df['boxing'] = df['description'].apply(extract_data_from_description, args=(boxing_type, boxing_type_mapping))
    df['size'] = df['description'].apply(extract_data_from_description, args=(size_type, size_type_mapping))
    df['cook_method'] = df['description'].apply(
        extract_data_from_description,
        args=(cook_method_type, cook_method_type_mapping)
    )
    return df
