from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.telegram_bot.constants import RESET_DIALOG


def create_standard_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=RESET_DIALOG)
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,  # Не скрывать кнопку после нажания
        is_persistent=True  # Показывать кнопки постоянно
    )
