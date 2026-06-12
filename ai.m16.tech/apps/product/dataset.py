"""
Загрузка датасета

Метод load_dataset загружает датасет. Сохраняет словари для признаков продукта и текста. Возвращает датасет для обучения
и тестирования, словари для признаков продуктов и текста.
Метод load_tokenizer загружает словари для текста и признаков продуктов.
Метод text_to_tensor преобразует строки в тензор.
Метод tensor_to_text преобразует тензор в строку.

@author Sergey Goncharov
"""
import io
import json
import random

import numpy as np
import pandas as pd
import torch
from pandas import DataFrame
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
from torch import Tensor
from torch.utils.data import TensorDataset

from product.tokenizer import TokenizerWord
from product.utility import cleaning_text, series_to_tensor, limit_category

DIR_DATA = 'apps/product/data'


def dataset_target(df: DataFrame, bert_name: str, name: str, save: bool = False) -> (Tensor, Tensor, TokenizerWord):
    """
    Создание набора данных признаков продуктов

    :param df: датасет
    :param name: название модели
    :param save: сохранить словари для признаков продуктов
    :return:
    """
    df_target = df[name]
    # токенизация элементов
    tokenizer_target = TokenizerWord(df_target)
    if save:
        tokenizer_target.save(DIR_DATA + '/model/' + bert_name + '/tokenizer_' + name + '.json')
    df_target = df_target.map(lambda it: tokenizer_target.tokens(it)[0:1])

    df_target = series_to_tensor(df_target)

    # разделение на обучающие и тестовые данные
    df_target1_train, df_target1_val = train_test_split(df_target, test_size=0.2, shuffle=False)

    return df_target1_train, df_target1_val, tokenizer_target


def ice_status(df: DataFrame, max_length: int):
    """
    Повторить датасет с ice_status
    """
    df_cp = df.copy()

    df_cp = df_cp[~df_cp['ice_status'].isin(['зам.', 'охл.'])]

    len_df = int(len(df_cp) / 2)
    df_frozen = df_cp[0:len_df].reset_index()
    df_chilled = df_cp[len_df:].reset_index()

    def add_random_words(words):
        def add_random(text):
            text_list = text.split(' ')
            rand_word_index = random.randrange(0, len(words) - 1)
            word = words[rand_word_index]
            text_len = len(text_list)
            if text_len <= 1:
                text_list.append(word)
            else:
                rand_index = random.randrange(0, text_len - 1)
                text_list.insert(rand_index, word)
                text_list = text_list[0:max_length]
            return ' '.join(text_list)

        return add_random

    df_frozen['text'] = df_frozen['text'].map(add_random_words(['замороженная', 'зам', 'замороженное']))
    df_frozen['ice_status'] = 'зам.'

    df_chilled['text'] = df_chilled['text'].map(add_random_words(['охлажденная', 'охл', 'охлажденное']))
    df_chilled['ice_status'] = 'охл.'

    df = pd.concat([df_frozen, df_chilled])

    return df


def gost_ty(df: DataFrame, max_length: int):
    """
    Повторить датасет с Гост и Ту
    """
    df_cp = df.copy()

    len_df = int(len(df_cp) / 2)
    df_gost = df_cp[0:len_df].reset_index()
    df_ty = df_cp[len_df:].reset_index()

    def add_random_word(word):
        def add_random(text):
            text_list = text.split(' ')
            text_len = len(text_list)
            if text_len <= 1:
                text_list.append(word)
            else:
                rand_index = random.randrange(0, text_len - 1)
                text_list.insert(rand_index, word)
                text_list = text_list[0:max_length]
            return ''.join(text_list)

        return add_random

    df_gost['text'] = df_gost['text'].map(add_random_word('гост'))
    df_gost['gost'] = 'Гост'

    df_ty['text'] = df_ty['text'].map(add_random_word('ту'))
    df_ty['ty'] = 'Ту'

    df = pd.concat([df_gost, df_ty])

    return df


def empty_line(df):
    """
    Добавить пустые строки в датасет
    """
    df_len = int(len(df) / 10)
    df_empty = df[0:df_len].copy().reset_index()
    df_empty['text'] = ''
    df_empty['mtype'] = '-'
    df_empty['part'] = '-'
    df_empty['ice_status'] = '-'
    df_empty['gost'] = '-'
    df_empty['ty'] = '-'

    return df_empty


def creating_dataset(df, bert_name: str, train_params, save_model, tokenizer):
    """
    Создание датасета
    """
    text_train, text_val = train_params
    # Наборы данных для признаков продуктов
    df_target1_train, df_target1_val, tokenizer_target1 = dataset_target(df, bert_name, 'mtype', save_model)
    df_target2_train, df_target2_val, tokenizer_target2 = dataset_target(df, bert_name, 'part', save_model)
    df_target3_train, df_target3_val, tokenizer_target3 = dataset_target(df, bert_name, 'ice_status', save_model)
    df_target4_train, df_target4_val, tokenizer_target4 = dataset_target(df, bert_name, 'gost', save_model)
    df_target5_train, df_target5_val, tokenizer_target5 = dataset_target(df, bert_name, 'ty', save_model)

    # Словари для признаков продуктов
    tokenizer_targets = (tokenizer_target1, tokenizer_target2, tokenizer_target3, tokenizer_target4, tokenizer_target5)

    if save_model:
        df_target_val = (df_target1_val, df_target2_val, df_target3_val, df_target4_val, df_target5_val)
        save_text_val(text_val, bert_name, tokenizer, df_target_val, tokenizer_targets)

    # Создание датасета для обучения
    dataset_train = TensorDataset(
        text_train,
        df_target1_train,
        df_target2_train,
        df_target3_train,
        df_target4_train,
        df_target5_train
    )
    # Создание тестового датасета
    dataset_val = TensorDataset(
        text_val,
        df_target1_val,
        df_target2_val,
        df_target3_val,
        df_target4_val,
        df_target5_val
    )

    return dataset_train, dataset_val, tokenizer_targets


def load_dataset(path: str, max_length: int, save_model: bool, bert_name: str):
    """
    Загрузка датасета
    """
    df = pd.read_csv(path, sep=';', on_bad_lines='skip')
    df = df.drop(columns=['id', 'date_mod', 'уточнение 1', 'уточнение 2'])
    df = shuffle(df)

    df = df.loc[df['text'].notnull()]
    df = df.loc[df['mtype'].notnull()]
    df = df.loc[df['part'].notnull()]

    df.loc[df.ice_status.isna(), 'ice_status'] = '-'
    df.loc[df.gost.isna(), 'gost'] = '-'
    df.loc[df.ty.isna(), 'ty'] = '-'

    df = limit_category(df, 'mtype', 500)
    df = limit_category(df, 'part', 100)
    df = limit_category(df, 'ice_status', 100)

    df['gost'] = '-'
    df['ty'] = '-'
    df_ice_status = ice_status(df, max_length)
    df_gost_ty = gost_ty(df, max_length)
    df_empty = empty_line(df)

    df = pd.concat([df, df_ice_status, df_gost_ty, df_empty])
    df = shuffle(df).reset_index()

    tokenizer = torch.hub.load('huggingface/pytorch-transformers', 'tokenizer', bert_name)

    arr_text = np.zeros((df['text'].shape[0], max_length))
    for index1, text in enumerate(df['text'].values):
        text = cleaning_text(text)
        encoded_input = tokenizer.encode(text, max_length=max_length, truncation=True, add_special_tokens=True)
        for index2, index in enumerate(encoded_input):
            arr_text[index1, index2] = index

    df_text = torch.Tensor(arr_text).type(torch.LongTensor)

    # разделение на обучающие и тестовые данные
    text_train, text_val = train_test_split(df_text, test_size=0.2, shuffle=False)
    train_params = (text_train, text_val)
    return creating_dataset(df, bert_name, train_params, save_model, tokenizer)


def tensor_to_text(text_index: Tensor, tokenizer) -> str:
    """
    Преобразовать тензор в строку
    """
    text_list = [tokenizer.decode(index.item()) for index in text_index]
    text_list = filter(lambda word: word != '<unk>', text_list)
    return " ".join(text_list)


def save_text_val(text: Tensor, bert_name: str, tokenizer, df_target_val, tokenizer_targets):
    """
    Сохранить тестовые данные
    """
    text_list = [tensor_to_text(text_index, tokenizer) for text_index in text]

    def get_target_str(n_target: int, item_index: int):
        target_index = df_target_val[n_target][item_index].item()
        return tokenizer_targets[n_target].index2word[target_index]

    list_data = []
    for index, text_str in enumerate(text_list):
        item = {
            'index': index,
            'text': text_str,
            'mtype': get_target_str(0, index),
            'part': get_target_str(1, index),
            'ice_status': get_target_str(2, index),
            'gost': get_target_str(3, index),
            'ty': get_target_str(4, index),
        }
        list_data.append(item)

    path = DIR_DATA + '/model/' + bert_name + '/text_val.json'
    with io.open(path, 'w', encoding='utf-8') as file:
        file.write(json.dumps(list_data))


def load_tokenizer(bert_name: str):
    """
    Загрузка словарей для текста и признаков продуктов
    """
    tokenizer = torch.hub.load('huggingface/pytorch-transformers', 'tokenizer', bert_name)
    tokenizer_target1 = TokenizerWord(path=DIR_DATA + '/model/' + bert_name + '/tokenizer_mtype.json')
    tokenizer_target2 = TokenizerWord(path=DIR_DATA + '/model/' + bert_name + '/tokenizer_part.json')
    tokenizer_target3 = TokenizerWord(path=DIR_DATA + '/model/' + bert_name + '/tokenizer_ice_status.json')
    tokenizer_target4 = TokenizerWord(path=DIR_DATA + '/model/' + bert_name + '/tokenizer_gost.json')
    tokenizer_target5 = TokenizerWord(path=DIR_DATA + '/model/' + bert_name + '/tokenizer_ty.json')

    tokenizer_targets = (tokenizer_target1, tokenizer_target2, tokenizer_target3, tokenizer_target4, tokenizer_target5)

    return tokenizer, tokenizer_targets


def text_to_tensor(text: str, tokenizer, max_length: int) -> Tensor:
    """
    Преобразование строки в тензор
    """
    text = cleaning_text(text)
    # indexes = tokenizer.encode(text)
    indexes = tokenizer.encode(text, max_length=max_length, truncation=True, add_special_tokens=True)
    # indexes = pad_indexes(indexes, max_length)
    return torch.Tensor(indexes).type(torch.LongTensor)


def load_text_val() -> list:
    """
    Загрузить тестовые данные
    """
    path = DIR_DATA + '/ds/texts.json'
    with open(path, encoding='utf-8') as file:
        data = json.load(file)

    return data
