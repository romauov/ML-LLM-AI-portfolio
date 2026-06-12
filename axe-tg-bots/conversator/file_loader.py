"""
загрузка прайс-листа и регламента для работы ассистента

@author Sergei Romanov
"""
import json
import re
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from openai import OpenAI
from utils.logger import logger as log
from utils.settings import secrets as s


def create_promt(promt_table, first_col):

    filtered_df = promt_table[~first_col.astype(
        str).str.lower().str.contains('buttons|placeholder')]
    client = OpenAI(
        base_url=s.openai_proxy,
        api_key=s.openai_key
    )
    promt_values = json.dumps(filtered_df.to_markdown(), ensure_ascii=False)
    system_promt = """
    "Ты — Prompt Engineer Bot. Твоя задача — помогать пользователям создать максимально эффективные промты для ИИ (например, ChatGPT, Midjourney, Claude).
    Тебе передают входные данные из которых нужно извлечь всю информацию для создания промта.

    После извлечения данных, сгенерируй финальный промт.
    Твой ответ должен содержать только финальный промт, никаких дополнительных комментариев не допускается
    """
    response = client.chat.completions.create(
        model='google/gemini-2.5-flash-pre-05-20',
        messages=[
            {
                "role": "system", "content": system_promt},
            {"role": "user", "content": f'входные данные: {promt_values}'}
        ],
        temperature=0.1,
        extra_headers={"X-title": "axe-tg-promt"}
    )

    reglament = response.choices[0].message.content

    return reglament


def get_buttons(promt_table, first_col):
    buttons = promt_table[first_col.astype(
        str).str.lower().str.contains('buttons')].iloc[0, 1]
    buttons = buttons.split(', ')
    return buttons


def extract_tools(first_col):
    pattern = r'\[tool\]\[(\w+)\]'

    tools = []
    for text in first_col:
        found = re.findall(pattern, str(text))
        tools.extend(found)
    return tools

def get_placeholder(promt_table, first_col):
    placeholder = promt_table[first_col.astype(
        str).str.lower().str.contains('placeholder')].iloc[0, 1]
    return placeholder


def load_from_google_sheet(table_id, sheet_name):

    SERVICE_ACCOUNT_FILE = 'google_credentials.json'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = build('sheets', 'v4', credentials=creds, cache_discovery=False)

    result = service.spreadsheets().values().get(
        spreadsheetId=table_id,
        range=f"'{sheet_name}'!A:Z"
    ).execute()

    values = result.get('values', [])
    if not values:
        log.error(f'No data in {table_id} - {sheet_name}')
    else:
        return pd.DataFrame(values[1:], columns=values[0])


def load_files(table_id, sheet_id, price_id=None, price_sheet=None):
    promt_table = load_from_google_sheet(table_id, sheet_id)
    promt_table = promt_table.iloc[:, 0:2]
    first_col = promt_table.iloc[:, 0]

    conversator_data = {}
    conversator_data['buttons'] = get_buttons(promt_table, first_col)
    conversator_data['reglament'] = create_promt(promt_table, first_col)
    conversator_data['tools'] = extract_tools(first_col)
    if price_id is not None and price_sheet is not None:
        conversator_data['price_list'] = load_from_google_sheet(
            price_id, price_sheet)
    conversator_data['placeholder'] = get_placeholder(promt_table, first_col)
    return conversator_data
