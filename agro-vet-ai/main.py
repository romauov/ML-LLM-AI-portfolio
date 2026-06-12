import asyncio
import sys

from dotenv import load_dotenv

# from app.telegram_bot.bot import run_telegram_bot
from app.utils.logger import get_logger
from app.web_api import run_web_api

app_logger = get_logger(__name__)

# Загрузка переменных окружения
load_dotenv()


# async def run_both_services():
#     """Запуск Telegram-бота и API-сервера одновременно."""
#     await asyncio.gather(
#         run_telegram_bot(),
#         run_web_api()
#     )


def parse_mode_from_args():
    """
    Получение режима запуска из аргументов командной строки.
    Возвращает строку-режим или пустую строку, если не задано.
    """
    return sys.argv[1] if len(sys.argv) > 1 else ""


def main():
    """Главная функция для запуска сервисов."""
    mode = parse_mode_from_args()

    if mode == "" or mode == "both":
        app_logger.info("Запуск только API-сервиса.")
        asyncio.run(run_web_api())
    # elif mode == "telegram":
    #     app_logger.info("Запуск только Telegram-сервиса.")
    #     asyncio.run(run_telegram_bot())
    elif mode == "api":
        app_logger.info("Запуск только API-сервиса.")
        asyncio.run(run_web_api())
    else:
        app_logger.error("Неизвестный режим. Используйте: telegram или api")
        sys.exit(1)


if __name__ == "__main__":
    main()
