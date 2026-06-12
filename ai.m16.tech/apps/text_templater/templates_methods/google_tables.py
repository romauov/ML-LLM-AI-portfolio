"""
Модуль работы с гугл-таблицами

@author Marat Ibatullin
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def table_init_gigachat():
    """
        Функция подключения к сервису гугл таблиц.

        Возвращает лист с оценками дял гига-чата.
    """
    json_key_file = 'apps/text_templater/templates_methods/tables-for-llm-metrcis-1-9632561dab77.json'
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_key_file, scope)
    client = gspread.authorize(creds)
    # pylint: disable=no-member
    sheet = client.open_by_url(
        'https://docs.google.com/spreadsheets/d/1ltMvTDncfmbbfXF6wOIj1xk2RluFY6n0tHQIPhwBUv0/edit#gid=0'
        ).worksheet('Giga_chat_desc')
    return sheet

def update_table(sheet, promt, answer):
    """
        Функция заполнения таблицы

        Ищет свободные ячейки в 1 и 2 столбцах,
        Затем заполняет их.
        
        Принимает:
        sheet: sheet - подключение к необходимому листу
        promt: str - строка с промтом к модели
        answer: str - строка с ответом модели
    """
    cell_list = sheet.findall(promt)
    if len(cell_list) == 0:
        first_col_len = len(sheet.col_values(1))
        if first_col_len + 1 < 1000:
            sheet.update_cell(first_col_len + 1, 1, promt)
            sheet.update_cell(first_col_len + 1, 2, answer)
            sheet.format('A1:A1000', {"wrapStrategy": "WRAP"})
