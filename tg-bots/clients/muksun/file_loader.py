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
        df = pd.read_excel(f'{path}/price_list.xls', skiprows=1)
        df = df.drop(
            columns=[col for col in df.columns if 'unnamed' in col.lower()])
        df = df.dropna(axis=1, how='all')
        df = df.loc[df.drop(df.columns[0], axis=1).dropna(how='all').index]
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
