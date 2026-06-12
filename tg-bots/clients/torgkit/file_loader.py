"""
загрузка прайс-листа и регламента для работы ассистента

@author Sergei Romanov
"""
import requests
import tabula

def load_files(text_id, path):
    """ загрузка прайс-листа и регламента

    Args:
        text_id (str): id гугл-документа с регламентов
        path (str): путь с расположением папки
    Returns:
        object, object: прайс-лист и регламент
    """
    try:
        df = tabula.read_pdf(f'{path}/torgkit_pricelist.pdf', pages="all")[0]
        df = df.drop(['Unnamed: 0', 'Unnamed: 1'], axis=1)
        df.columns = df.iloc[0].index
        df = df.iloc[1:]
        df = df.dropna()
    except FileNotFoundError:
        df = None
    
    REGLAMENT_URL = f'https://docs.google.com/document/d/{text_id}/export?format=txt'
    my_file = requests.get(REGLAMENT_URL, timeout=30)
    with open(f'{path}/reglament.txt', 'wb') as some_file:
        some_file.write(my_file.content)
    with open(f'{path}/reglament.txt', encoding='utf-8-sig') as some_file:
        reglament = some_file.readlines()
    reglament = ''.join(reglament)
    
    return df, reglament
