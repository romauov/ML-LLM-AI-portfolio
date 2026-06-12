"""
загрузка регламента для работы ассистента

@author Nikolay Zhabchikov
"""
import requests


def load_files(text_id, path):
    """ загрузка регламента

    Args:
        text_id (str): id гугл-документа с регламентов
        path (str): путь с расположением папки
    Returns:
        object, object: прайс-лист и регламент
    """

    reglament_url = f'https://docs.google.com/document/d/{text_id}/export?format=txt'
    my_file = requests.get(reglament_url, timeout=30)
    with open(f'{path}/reglament.txt', 'wb') as some_file:
        some_file.write(my_file.content)
    with open(f'{path}/reglament.txt', encoding='utf-8-sig') as some_file:
        reglament = some_file.readlines()
    reglament = ''.join(reglament)

    return reglament
