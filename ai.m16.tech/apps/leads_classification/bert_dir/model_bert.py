"""
Загрузка и подготовка модели

@author Dmitry Avzalov, Yaroslav Koltashev
"""
from transformers import BertTokenizer
from transformers import BertForSequenceClassification
import torch


def load_and_prepare_bert_model(model_path: str, num_classes: int) -> torch.nn.Module:
    """
    Загружает и подготавливает модель BERT для классификации последовательностей.

    Аргументы:
    - model_path (str): Путь к предобученной модели BERT.
    - num_classes (int): Количество классов для классификации последовательностей.

    Возвращает:
    - torch.nn.Module: Загруженная и подготовленная модель BERT.
    - tokenizer: Токенизатор для модели BERT.
    """
    tokenizer_path = 'cointegrated/rubert-tiny'
    tokenizer = BertTokenizer.from_pretrained(tokenizer_path)

    model = 'cointegrated/rubert-tiny'
    model = BertForSequenceClassification.from_pretrained(model)
    out_features = model.bert.encoder.layer[1].output.dense.out_features
    model.classifier = torch.nn.Sequential(
        torch.nn.Linear(out_features, num_classes),
        torch.nn.Softmax()
    )
    # pylint: disable=bare-except
    try:
        model.load_state_dict(torch.load(model_path))
    except:
        model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')), strict=False)

    return model, tokenizer
