"""
Utility функции

@author Sergey Goncharov
"""
import io
import json
import re

import numpy as np
import torch
from pandas import Series, DataFrame
from ruamel.yaml import YAML
from torch import Tensor


def cleaning_text(text: str):
    """
    Удаляет из текста лишние слова
    """
    if isinstance(text, str):
        text = text.lower()
        text = text.strip()
        text = re.sub("\n", " ", text)
        text = re.sub(r"\,", " ", text)
        text = re.sub(r"[^а-я0-9|\s]", "", text)

        text = re.sub(r"\sкг|руб|рубкг|ркг\s", " ", text)
        text = re.sub(r"\sкг|руб|рубкг|ркг$", "", text)
        text = re.sub(r"^кг|руб|рубкг|ркг\s", "", text)

        text = re.sub(r"\s[а-я{1}]\s", " ", text)
        text = re.sub(r"\s[а-я{1}]$", "", text)
        text = re.sub(r"^[а-я{1}]\s", "", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
    return text


def series_to_tensor(input_data: Series) -> Tensor:
    """
    Преобразование объекта Series в Tensor. Сохраняет тип данных в LongTensor
    """
    d_1 = len(input_data)
    d_2 = len(input_data.iloc[0])
    data = np.full((d_1, d_2), 1)

    for x, row in enumerate(input_data):
        for y, cell in enumerate(row):
            data[x, y] = float(cell)
    tensor = torch.Tensor(data).type(torch.LongTensor)
    return tensor


PAD_IDX = 0


def pad_indexes(indexes: list, max_length: int) -> list:
    """
    Добавление PAD_IDX в список до размера MAX_LENGTH

    :param indexes: последовательность индексов
    :param max_length: длина
    :return: последовательность индексов новой длины
    """
    indexes = indexes[0:max_length]
    return indexes + ([PAD_IDX] * (max_length - len(indexes)))


def limit_category(df: DataFrame, product: str, limit: int) -> DataFrame:
    """
    Фильтрация категорий признаков продукта, количество образцов больше чем лимит

    :param df: датасет
    :param product: продукт
    :param limit: лимит
    :return: датасет
    """
    category_count = df.groupby(product)[product].size().to_frame()
    category_top = category_count[category_count[product] > limit][product]
    category_top = category_top.keys().tolist()

    return df[df[product].isin(category_top)]


def load_params():
    """
    Загрузить параметры модели из файла params.yaml
    """
    yaml = YAML(typ="safe")
    with open("apps/product/params.yaml", encoding='utf-8') as file:
        params = yaml.load(file)
    return params


def save_metrics(data: dict):
    """
    Сохранить метрику обучения
    """
    path = 'apps/product/data/metrics.json'
    with io.open(path, 'w', encoding='utf-8') as file:
        file.write(json.dumps(data))
