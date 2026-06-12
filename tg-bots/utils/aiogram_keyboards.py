"""
клавиатуры aiogram

@author Sergei Romanov
"""
import json
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

base_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='помощь с ботом')]],
    resize_keyboard=True,
    input_field_placeholder='Задайте свой вопрос или нажите кнопку ниже для помощи'
    )

async def extended_kb(query_examples, adjust=2):
    """создание клавиатуры

    Returns:
        object: объект с экранной клавиатурой aiogram
    """
    keyboard = ReplyKeyboardBuilder()
    for q in query_examples:
        keyboard.add(KeyboardButton(text=q))
    return keyboard.adjust(adjust).as_markup(resize_keyboard=True,
                                        input_field_placeholder='Задайте свой вопрос или выберите один из предложенных примеров')

async def model_kb():
    keyboard = ReplyKeyboardBuilder()
    with open('model_rates.json') as f:
        rates = json.load(f)
        for model in rates:            
            keyboard.add(KeyboardButton(text=f'{model}    ${rates[model][0] * 1_000_000} ${rates[model][1] * 1_000_000}'))
    return keyboard.adjust(1).as_markup(resize_keyboard=True,
                                        input_field_placeholder='Выберите модель')
