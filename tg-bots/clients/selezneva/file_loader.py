"""
загрузка прайс-листа и регламента для работы ассистента

@author Sergei Romanov
"""
from docx import Document
import requests
import pandas as pd

def load_files(table_id, text_id, path):
    """ загрузка прайс-листа и регламента

    Args:
        table_id (str): id гугл-таблицы с прайс-листом
        text_id (str): id гугл-документа с регламентов
        path (str): путь с расположением папки
    Returns:
        object, object: прайс-лист и регламент
    """        
    PRICE_LIST_URL = f'https://docs.google.com/spreadsheets/d/{table_id}/export?gid=0&format=csv'
    REGLAMENT_URL = f'https://docs.google.com/document/d/{text_id}/export?format=txt'
    price_list = pd.read_csv(PRICE_LIST_URL)
    price_list.to_excel(f'{path}/pricelist_selezneva_fish.xlsx')
    price_list.loc[:, 'product'] = price_list['Категория продукции'].apply(lambda x: ' '.join(x.split()[:2])) + ' ' + price_list['Вид продукции']
    price_list.drop(['Категория продукции', 'Вид продукции'], axis=1, inplace=True)
    my_file = requests.get(REGLAMENT_URL, timeout=30)
    with open(f'{path}/reglament.txt', 'wb') as some_file:
        some_file.write(my_file.content)
    with open(f'{path}/reglament.txt', encoding='utf-8-sig') as some_file:
        reglament = some_file.readlines()
    reglament = ''.join(reglament)
    produсts = price_list['product'].unique().tolist()
    reglament += f'Список продуктов в наличии - {produсts}'
    return price_list, reglament
