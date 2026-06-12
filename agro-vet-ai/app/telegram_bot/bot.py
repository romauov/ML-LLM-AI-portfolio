import asyncio

from aiogram import Bot, Dispatcher
from app.db.db import create_engine, create_session_factory
from app.db.user_model import User
from app.db.drugs_model import Drug
from app.middlewares.db_middleware import DbMiddleware
from app.telegram_bot.handlers import commands
from app.telegram_bot.handlers.messages import router as messages_router
from app.utils.logger import get_logger
from app.utils.settings import secrets as s

app_logger = get_logger(__name__)

API_TOKEN = s.api_token


# === Иинициализация БД ===
async def init_database():
    """Инициализация базы данных"""
    engine = await create_engine()
    session_factory = await create_session_factory(engine)
    user_db = User(session_factory)
    drug_db = Drug(session_factory)
    app_logger.info("База данных инициализирована")
    return engine, user_db, drug_db


# === Запуск Telegram бота ===
async def run_telegram_bot():
    """Запуск только Telegram бота"""
    app_logger.info("Запуск Telegram бота...")
    engine, user_db, drug_db = await init_database()

    # Инициализация бота и диспетчера
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(commands.router)  # Роутеры из `commands.py` - обработчик команд из телеграма
    dp.include_router(messages_router)  # Подключаем роутеры для текстовых сообщений

    # Добавляем мидлварь для передачи user_db (drug_db оставлен для совместимости)
    dp.update.middleware(DbMiddleware(user_db, drug_db))

    # Удаляем вебхук, если он был
    await bot.delete_webhook(drop_pending_updates=True)

    # Запускаем long polling
    try:
        await dp.start_polling(bot)
    finally:
        await engine.dispose()  # Закрываем соединения после завершения работы


def main():
    """Главная функция для запуска Telegram бота."""
    app_logger.info("Запуск Telegram-сервиса.")
    asyncio.run(run_telegram_bot())


if __name__ == "__main__":
    main() 