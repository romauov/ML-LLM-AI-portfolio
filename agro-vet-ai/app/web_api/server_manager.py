import uvicorn

from app.web_api.app import create_app
from app.agents.router.agent import TopicRouterAgent
from app.utils.logger import get_logger

app_logger = get_logger(__name__)


class WebAPIServerManager:
    """Менеджер для управления Web API сервером"""

    def __init__(self):
        self.topic_router = None
        self.knowledge_base = None
        self.app = None
        self.server = None

    def initialize_topic_system(self):
        """Инициализация системы топиков"""
        self.agent_router = TopicRouterAgent()

    def create_application(self):
        """Создание FastAPI приложения"""
        self.app = create_app()
        app_logger.info("FastAPI приложение создано")

    async def run_server(self, host="0.0.0.0", port=8000):
        """Запуск web API сервера"""
        app_logger.info("Запуск FastAPI сервера...")

        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="warning",  # Уменьшаем уровень логирования uvicorn
            access_log=False  # Отключаем access логи uvicorn
        )
        self.server = uvicorn.Server(config)

        try:
            await self.server.serve()
        except Exception as e:
            app_logger.error(f"Ошибка при запуске сервера: {e}")
            raise
