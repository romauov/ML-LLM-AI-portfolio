"""
загрузка прайс-листа и регламента для работы ассистента

@author Sergei Romanov
"""
import requests
import pandas as pd

def load_files(text_id, path):
    """ загрузка прайс-листа и регламента

    Args:
        text_id (str): id гугл-документа с регламентов
        path (str): путь с расположением папки
    Returns:
        object, object: прайс-лист и регламент
    """
    try:   
        df = pd.read_excel(f'{path}/price_list.xlsx', header=8)
        df = df.drop(columns=[col for col in df.columns if 'unnamed' in col.lower()])
        df = df.dropna(axis=1, how='all')
        df = df.loc[df.drop(df.columns[0], axis=1).dropna(how='all').index]
        df['product'] = df[df.columns[0]].apply(lambda x: x.replace('ЦБ', 'ЦБ(цыплята бройлерные') if 'ЦБ' in x else x)
        df['halal'] = df['product'].apply(lambda x: 'да' if 'халяль' in x.lower() else 'нет')
    except:
        df = None
    
    REGLAMENT_URL = f'https://docs.google.com/document/d/{text_id}/export?format=txt'
    my_file = requests.get(REGLAMENT_URL, timeout=30)
    with open(f'{path}/reglament.txt', 'wb') as some_file:
        some_file.write(my_file.content)
    with open(f'{path}/reglament.txt', encoding='utf-8-sig') as some_file:
        reglament = some_file.readlines()
    reglament = ''.join(reglament)
    
    return df, reglament
