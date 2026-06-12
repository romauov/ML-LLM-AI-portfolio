"""
генерация ответа от YandexLLM

@author Sergei Romanov
"""
import os
import requests
from api.userdata import fetch_user_data
from gpt.client import client


async def generate_promt_gpt(request):
    """создание промта из пользовательских данных

    Args:
        request (pydantic object): объект с данными запроса

    Returns:
        str: промт для LLM
    """
    system_details = await fetch_user_data(request.site, request.system_id)
    if request.user_id != 0:
        user_details = await fetch_user_data(request.site, request.user_id)
    else:
        user_details = False

    if request.reglament_id is None or request.reglament_id == '':
        reglament = f"Ты цифровой помощник"
        if 'company_title' in system_details:
            reglament += f" в компании {system_details['company_title']}, которая занимается {system_details['company_description']}"
        reglament += f", ты подготавливаешь быстрые ответы на электронные сообщения для {system_details['position']}. "

        if user_details:
            reglament += f"Тебе приходят сообщения от {user_details['position']}"
            if 'company_title' in user_details:
                reglament += f" из компании {user_details['company_title']}, которая занимается {user_details['company_description']}"

        reglament += ". Вы отправили пользователю сообщение с предложением о продаже товара и получили от него ответ, твоя задача проанализировать его реакцию и подготовить ответное сообщение."

    else:
        REGLAMENT_URL = f'https://docs.google.com/document/d/{request.reglament_id}/export?format=txt'
        my_file = requests.get(REGLAMENT_URL, timeout=30)
        with open('reglament.txt', 'wb') as some_file:
            some_file.write(my_file.content)
        with open('reglament.txt', encoding='utf-8-sig') as some_file:
            reglament = some_file.readlines()
        reglament = ''.join(reglament)
        os.remove('reglament.txt')

        extra_promt = f"ты подготавливаешь быстрые ответы на электронные сообщения для {system_details['position']}. "
        reglament = reglament.format(extra_promt)

        if user_details:
            reglament += f"\nТебе приходят сообщения от {user_details['position']}"
            if 'company_title' in user_details:
                reglament += f" из компании {user_details['company_title']}, которая занимается {user_details['company_description']}"

        reglament += "Вы отправили пользователю сообщение с предложением о продаже товара и получили от него ответ, твоя задача проанализировать его реакцию и подготовить ответное сообщение."
    messages = [
        {
            "role": "system",
            "content": reglament
        }
    ]
    return messages


async def generate_qr_gpt(request):
    """генерация ответа Chat GPT

    Args:
        request (pydantic object): объект с данными запроса

    Returns:
        str: сгенерированный ответ Chat GPT
    """
    messages = await generate_promt_gpt(request)
    messages.extend(request.messages)

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        extra_headers={"X-title": "email-bot"}
    )
    response_message = response.choices[0].message

    return response_message.content
