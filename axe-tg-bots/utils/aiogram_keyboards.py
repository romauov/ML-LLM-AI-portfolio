from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

async def extended_kb(query_examples, placeholder, adjust=2):
    """создание клавиатуры

    Returns:
        object: объект с экранной клавиатурой aiogram
    """
    keyboard = ReplyKeyboardBuilder()
    for q in query_examples:
        keyboard.add(KeyboardButton(text=q))
    return keyboard.adjust(adjust).as_markup(resize_keyboard=True,
                                        input_field_placeholder=placeholder)