from app.db.db import create_engine, create_session_factory
from app.db.database_manager import DatabaseManager
from app.web_api.server_manager import WebAPIServerManager
from app.utils.logger import get_logger

app_logger = get_logger(__name__)


async def run_web_api():
    """Запуск только FastAPI сервера."""
    app_logger.info("Запуск FastAPI сервера...")

    # Инициализация БД
    engine = await create_engine()
    session_factory = await create_session_factory(engine)
    db_manager = DatabaseManager()
    await db_manager.initialize(engine, session_factory)

    # Инициализация и запуск web API
    web_api_manager = WebAPIServerManager()
    web_api_manager.initialize_topic_system()
    web_api_manager.create_application()

    try:
        await web_api_manager.run_server()
    finally:
        await db_manager.close()
