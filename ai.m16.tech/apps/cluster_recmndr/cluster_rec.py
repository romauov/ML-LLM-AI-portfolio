"""
Сервис для поиска клиентов, взаимодействоваших с кластером, к которому относится запрашиваемый вид продукции.
Приложение определяет ближайшие к запросу виды продукции, определяет их кластеры и выдаёт список пользователей, 
взаимодействоваших с этим кластером в хронологическом порядке

example_input = {
    "type1": 'форель',
    "type2": 'разделка',
    "category_name": 'Разделка' (не обязательно),
    "number_of_users": 100
}

example_output = {'user_ids': 
    [121073, 154047, ...]
}

@author Sergei Romanov
"""
import numpy as np
import pandas as pd
import polars as pl
import torch

from functools import lru_cache
from sklearn.metrics.pairwise import cosine_distances
from transformers import AutoTokenizer, AutoModel

BASE = 'apps/file_hosting/cluster_recmndr'
EMBEDDINGS_DIR = 'apps/file_hosting/knn_recommendations'

CLUSTERS_CSV = f'{BASE}/clusters.csv'
USERSTAT_CSV = f'{BASE}/userStat_f.csv'
LABELS_CSV = f'{BASE}/labels_categories.csv'
EMAILS_CSV = f'{EMBEDDINGS_DIR}/user_emails.csv'
MAILLIST_CSV = f'{EMBEDDINGS_DIR}/maillisted_users.csv'
SPAMERS_CSV = f'{EMBEDDINGS_DIR}/spamers.csv'
BERT_PATH = f'{BASE}/bert'
CACHE_DIR = f'{BASE}/cache'

_model = None
_tokenizer = None

def _load_model():
    global _model, _tokenizer
    if _model is not None:
        return
    try:
        _tokenizer = AutoTokenizer.from_pretrained(BERT_PATH, cache_dir=CACHE_DIR)
        _model = AutoModel.from_pretrained(BERT_PATH, cache_dir=CACHE_DIR)
    except Exception:
        pretrained_weights = 'cointegrated/rubert-tiny2'
        _tokenizer = AutoTokenizer.from_pretrained(pretrained_weights, cache_dir=CACHE_DIR)
        _tokenizer.save_pretrained(BERT_PATH)
        _model = AutoModel.from_pretrained(pretrained_weights, cache_dir=CACHE_DIR)
        _model.save_pretrained(BERT_PATH)

@lru_cache(maxsize=1)
def _read_clusters():
    return pl.read_csv(CLUSTERS_CSV)

@lru_cache(maxsize=1)
def _read_userstat():
    return pl.read_csv(USERSTAT_CSV)

@lru_cache(maxsize=1)
def _read_emails():
    return pl.read_csv(EMAILS_CSV).filter(pl.col('site') == 'meatinfo').select(['userId', 'email'])

@lru_cache(maxsize=1)
def _read_maillisted():
    return pl.read_csv(MAILLIST_CSV)

@lru_cache(maxsize=1)
def _read_spamers():
    return pl.read_csv(SPAMERS_CSV)

@lru_cache(maxsize=1)
def _read_labels():
    return pd.read_csv(LABELS_CSV)

def get_embeddings(type1=None, type2=None, category_name=None):
    """
    Создание эмбеддинга входящего запроса

    Args:
        type1 (_type_, optional):  type1 из userStat. Defaults to None.
        type2 (_type_, optional): type2 из userStat. Defaults to None.
        category_name (_type_, optional): category_name из tradeBoard. Defaults to None.

    Returns:
        _type_: эмбеддинг запроса
    """
    _load_model()
    query = ' '.join([category_name, type1, type2])

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = _model.to(device)

    tok = _tokenizer(query, padding=True, truncation=True, return_tensors='pt')
    batch = tok['input_ids'].to(device)
    attention_mask = tok['attention_mask'].to(device)

    with torch.no_grad():
        batch_embeddings = model(batch, attention_mask=attention_mask)

    q_embedding = batch_embeddings[0][:, 0, :].cpu().numpy()

    return q_embedding

def get_clients(q_embedding):
    """Получение userId, взаимодействовавших с кластерром продукции в последнее время

    Args:
        q_embedding (_type_): эмбеддинг запроса

    Returns:
        _type_: список клиентов
    """
    clusters = _read_clusters()
    cliens_df = _read_userstat()

    embeddings = clusters.drop(['cluster', 'product']).to_numpy()
    similarities = cosine_distances(q_embedding, embeddings)[0]

    best_match = np.argsort(similarities)[:10]
    matched_clusters = set(clusters['cluster'][best_match].to_list())

    clients = cliens_df.filter(pl.col('cluster').is_in(matched_clusters)).select(pl.col(['userId', 'date'])).\
        group_by('userId').max().sort(by='date', descending=True).select(pl.col('userId'))['userId'].to_list()

    return clients

def join_emails(ids, number_of_users):
    """выгрузка и фильтрация имейлов

    Args:
        ids (lst): список пользователей для присоединения имейлов
        number_of_users (int): ограничение по количеству

    Returns:
        DataFrame: userId и email
    """
    emails_df = _read_emails()
    maillisted_users = _read_maillisted()
    spamers = _read_spamers()

    emails = emails_df.filter(
        ~pl.col('email').is_in(maillisted_users.filter(pl.col('site') == 'meatinfo')['email']),
        ~pl.col('email').is_in(spamers['email']),
        pl.col('userId').is_in(ids)
    ).to_pandas()[:number_of_users]

    return emails

def predict(type1, type2, category_name=None, number_of_users=100):
    """
    Получение списка клиентов, заинтересованных в типе продукции
    
    input_exapmles = [
        {'type1': "форель", 'type1': "разделка"},
        {'type1': "форель", 'type1': "разделка", "category_name": "Разделка", number_of_users: 100}    
    example_out_put = {"user_ids": clients_list}
    """
    # получение эмбеддинга запроса
    if category_name is None:
        categories_df = _read_labels()
        try:
            category_name = categories_df[categories_df['type1'] == type1.lower()]['category_name'].values[0]
        except IndexError:
            return {"error": f"{type1} не был найден в списке категорий продукции"}
    q_emb = get_embeddings(type1, type2, category_name)
    # получение и отправка списка клиентов
    clients = get_clients(q_emb)
    emails_df = join_emails(clients, number_of_users)
    return {
        'userIds': emails_df['userId'].to_list(),
        'emails': emails_df['email'].to_list()
        }
