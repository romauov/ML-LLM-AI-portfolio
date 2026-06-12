"""
Движок поиска похожих объявлений

@author Marat Ibatullin
"""

import faiss
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

def model_init(path="apps/bert_recommendations/model"):
    """
    Инициализация модели векторизации текста
    """
    tokenizer = AutoTokenizer.from_pretrained(path)
    model = AutoModel.from_pretrained(path)
    return model, tokenizer

def embed_bert_cls(text, model, tokenizer):
    """
    Векторизация входного текста

    arguments:
    text -- текст(строка) который необходимо векторизовать
    model, tokenizer -- LLM преобученные модели 

    возвращает массив эмбеддингов
    """
    tokes = tokenizer(text, padding=True, truncation=True, return_tensors='pt')
    with torch.no_grad():
        model_output = model(**{k: v.to(model.device) for k, v in tokes.items()})
    embeddings = model_output.last_hidden_state[:, 0, :]
    embeddings = torch.nn.functional.normalize(embeddings)
    return embeddings[0].cpu().numpy()

def get_emeddings(text):
    """
    Функция, векторизирующая данный массив текстов

    arguments:
    text -- массив текстов который необходимо векторизовать

    возвращает массив эмбеддингов для всего массива текстов
    """
    embeddings = []
    model, tokenizer = model_init("/app/apps/bert_recommendations/model")
    for _ in text:
        embeddings.append(embed_bert_cls(_, model, tokenizer))
    return embeddings

# pylint: disable=no-value-for-parameter
def index_init(embeddings_contexts: list, embeddings_search: list):
    """
    Инициализация движка векторного поиска(faiss.IndexFlatL2)

    arguments:
    embeddings_contexts -- массив эмбеддингов для текстов объявлений
    embeddings_search -- массив эмбеддингов для поисковых запросов

    возвращает движок, готовый для поиска по похожести(Евклидово расстояние)
    """
    dimension = len(embeddings_contexts[0])
    index_search = faiss.IndexFlatL2(dimension)
    index_adv = faiss.IndexFlatL2(dimension)

    index_search.add(embeddings_search)
    index_adv.add(embeddings_contexts)
    return index_adv, index_search

def search_for(faiss_index, _query: str, num_results: int = 10):
    """
    Поиск по обученному индексу

    arguments:
    faiss_index -- обученный движок поиска
    _query -- строка текста(объявление/поисковый запрос)
    num_results -- количество соседей (default 10)

    возвраащет массив индексов похожих объявлений в исходном массиве на 
    котором обучался движок поиска(см. arguments index_init())
    """
    model, tokenizer = model_init()
    query_embedding = embed_bert_cls(_query, model, tokenizer)
    query_vector = np.array([query_embedding]).astype('float32')
    _, indexes = faiss_index.search(query_vector, num_results) # pylint: disable=unused-variable
    output = []
    for i in range(len(indexes[0])):
        item = {
            'id': indexes[0][i],
        }
        output.append(item)
    return output

def set_found(staff: list, allstaff: list):
    """
    Подготовка текстов объявлений/поисковых запросов

    arguments:
    staff -- ID  объялений/поисковых запросов
    allstaff -- Массив объялений/поисковых запросов

    
    """
    goods = []
    for good in staff:
        goods.append(allstaff[good['id']])
    return goods

def set_found_polars(staff: list, allstaff):
    """
    Подготовка текстов объявлений/поисковых запросов

    arguments:
    staff -- ID  объялений/поисковых запросов
    allstaff -- Массив объялений/поисковых запросов

    
    """
    goods = []
    for good in staff:
        goods.append(allstaff.slice(good['id'], 1).item())
    return goods
    