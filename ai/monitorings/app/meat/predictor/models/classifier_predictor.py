"""
Скрипт для предсказания с помощью моделей классификации

@author Nikolay Zhabchikov
"""
import os

import numpy as np
import pandas as pd
import onnxruntime as ort
from tokenizers import Tokenizer

from app.meat.utils.data import categories_mapping

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'models')
DISTIL_BERT_ONNX = os.path.join(MODEL_PATH, 'bert', 'distilbert.onnx')
DISTIL_BERT_TOKENIZER = os.path.join(MODEL_PATH, 'bert', 'tokenizer.json')

PROVIDERS = ['CPUExecutionProvider']

options = ort.SessionOptions()
options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL

# bert bert model
bert_onnx = ort.InferenceSession(
    DISTIL_BERT_ONNX,
    sess_options=options,
    providers=PROVIDERS
)
tokenizer = Tokenizer.from_file(DISTIL_BERT_TOKENIZER)


def onnx_encode(text):
    """
    Кодирование текста в эмбеддинг с помощью bert модели distilbert
    Args:
        text: текст

    Returns:
        np.array: размера 1x768
    """
    inputs_tokens = tokenizer.encode(text)
    inputs = {
        'input_ids': np.expand_dims(np.array(inputs_tokens.ids, dtype=np.int64), axis=0),
        'attention_mask': np.expand_dims(np.array(inputs_tokens.attention_mask, dtype=np.int64), axis=0),
    }
    out = bert_onnx.run(None, inputs)
    emb = np.mean(out[7], axis=1)[0]
    return emb


def onnx_predict(model, df):
    """
    Предсказание класса bert моделью
    Args:
        model: InferenceSession объект модели
        df: DataFrame с признаками

    Returns:
        list(np.array, list(dict)): Список содержащий np.array с классами и список с словарем вероятностей
        для каждого предсказания
    """
    str_input = df['category'].values.reshape(-1, 1)
    float_input = df.drop('category', axis=1).values
    inputs = {'str_input': str_input, 'float_input': float_input}
    result = model.run(None, inputs)
    return result


def predict_on_classifier(df):
    """
    Предсказание product_type с помощью ml моделей.
    В качестве предсказания берется класс в котром обе модели дали одинаковое предсказание
    Args:
        df (DataFrame): датафрейм мониторинга

    Returns:
        DataFrame: датафрейм мониторинга с предсказаниями
    """
    to_preds_df = df[df['product_type'].isna()]

    for category in categories_mapping.keys():
        sub_df = to_preds_df[to_preds_df['product'].isin(categories_mapping[category])].copy()

        if sub_df.empty:
            continue

        embeddings = [onnx_encode(text) for text in sub_df['description_ls'].values]

        # обработка датасета под формат моделей
        input_df = pd.concat((sub_df.reset_index(), pd.DataFrame(embeddings)), axis=1)
        input_df = input_df.drop(['index', 'description', 'product_type', 'description_ls'], axis=1)
        input_df.columns = input_df.columns.astype(str)
        input_df['product'] = input_df['product'].apply(lambda x: x.lower())
        input_df.rename(columns={"product": "category"}, inplace=True)

        model_logreg = ort.InferenceSession(
            os.path.join(MODEL_PATH, 'logreg', category) + '.onnx',
            sess_options=options,
            providers=PROVIDERS
        )
        sub_df['logreg_preds'] = onnx_predict(model_logreg, input_df)[0]

        model_catboost = ort.InferenceSession(
            os.path.join(MODEL_PATH, 'catboost', category) + '.onnx',
            sess_options=options,
            providers=PROVIDERS
        )
        sub_df['catboost_preds'] = onnx_predict(model_catboost, input_df)[0]

        # оставляем предсказания только для совпадений двух моделей
        sub_df = sub_df[sub_df['logreg_preds'] == sub_df['catboost_preds']]
        to_preds_df.loc[sub_df.index, 'product_type'] = sub_df['catboost_preds']

    df.loc[to_preds_df.index, 'product_type'] = to_preds_df['product_type']
    return df
