import asyncio
import traceback
from asyncio import CancelledError

from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message
from app.utils.logger import get_logger

app_logger = get_logger(__name__)


async def update_loading(loading_message):
    """Обновляем анимацию загрузки."""
    dots = [".", "..", "..."]
    i = 0
    while True:
        await asyncio.sleep(1)
        i = (i + 1) % len(dots)
        try:
            await loading_message.edit_text(f"⌛{dots[i]}")
        except TelegramAPIError:
            break


async def create_wait_response_task(message):
    loading_message = await message.answer("⌛",  parse_mode="HTML")
    typing_task = asyncio.create_task(update_loading(loading_message))
    return loading_message, typing_task


async def cancel_wait_response_task(tasks):
    try:
        for task in tasks:
            if isinstance(task, asyncio.Task):
                task.cancel()
            elif isinstance(task, Message):
                await task.delete()

    except (TelegramAPIError, CancelledError):
        error_message = traceback.format_exc()
        app_logger.error(f"Ошибка при удалении сообщения ожидания ответа: {error_message}")
