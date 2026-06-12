"""
загрузка прайс-листа и регламента для работы ассистента

@author Sergei Romanov
"""
from docx import Document
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
        table = Document(f'{path}/price_list.docx').tables[0]
        data = [[cell.text for cell in row.cells] for row in table.rows]
        df = pd.DataFrame(data)
        df = df.rename(columns=df.iloc[0]).drop(df.index[0]).reset_index(drop=True)
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
