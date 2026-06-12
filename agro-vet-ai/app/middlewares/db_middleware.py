"""
Middleware для предоставления доступа к базам данных в обработчиках Telegram бота.
Автоматически добавляет объекты user_db и drug_db в контекст каждого обработчика.
"""
from app.db.user_model import User
from app.db.drugs_model import Drug
from aiogram.types import TelegramObject
from aiogram.dispatcher.middlewares.base import BaseMiddleware


class DbMiddleware(BaseMiddleware):
    """
    Middleware для автоматического предоставления доступа к базам данных.

    Usage: dp.middleware.setup(DbMiddleware(user_db, drug_db))
    """

    def __init__(self, user_db: User, drug_db: Drug):
        """Инициализация с объектами баз данных."""
        super().__init__()
        self.user_db = user_db
        self.drug_db = drug_db

    async def __call__(self, handler, event: TelegramObject, data: dict):
        """Добавляет объекты БД в контекст обработчика."""
        data["user_db"] = self.user_db
        data["drug_db"] = self.drug_db
        return await handler(event, data)
