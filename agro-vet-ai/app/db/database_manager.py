from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession
from app.db.user_model import User
from app.db.drugs_model import Drug
from app.utils.logger import get_logger

app_logger = get_logger(__name__)


class DatabaseManager:
    """Менеджер для управления базой данных и моделями"""

    def __init__(self):
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self.user_db: User | None = None
        self.drug_db: Drug | None = None

    async def initialize(self, engine: AsyncEngine, session_factory: async_sessionmaker[AsyncSession]):
        """Инициализация менеджера базы данных"""
        self.engine = engine
        self.session_factory = session_factory
        self.user_db = User(session_factory)
        self.drug_db = Drug(session_factory)

    async def close(self):
        """Закрытие соединений с базой данных"""
        if self.engine:
            await self.engine.dispose()
            app_logger.info("Соединения с базой данных закрыты")

    @property
    def session(self) -> async_sessionmaker[AsyncSession]:
        """Получение фабрики сессий"""
        if self.session_factory is None:
            raise RuntimeError("DatabaseManager не инициализирован")
        return self.session_factory

    @property
    def users(self) -> User:
        """Получение модели пользователей"""
        if self.user_db is None:
            raise RuntimeError("DatabaseManager не инициализирован")
        return self.user_db

    @property
    def drugs(self) -> Drug:
        """Получение модели лекарств"""
        if self.drug_db is None:
            raise RuntimeError("DatabaseManager не инициализирован")
        return self.drug_db 