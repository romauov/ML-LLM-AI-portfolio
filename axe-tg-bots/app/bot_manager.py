import asyncio
from typing import Dict, Optional

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy

from app.schemas import ClientData
from utils.logger import logger as log
from utils.middleware import UserThrottlingMiddleware


class BotManager:
    """Оптимизированный менеджер ботов"""

    def __init__(self, storage: Optional[MemoryStorage] = None, fsm_strategy: FSMStrategy = FSMStrategy.CHAT):
        self.clients: Dict[str, ClientData] = {}
        self.storage = storage or MemoryStorage()
        self.fsm_strategy = fsm_strategy

    async def add_and_start_client(self, client_data: ClientData) -> None:
        """Добавление, настройка и запуск клиента с полной обработкой ошибок"""
        # Проверка существования клиента
        if client_data.client_name in self.clients:
            # raise KeyError(f"Client {client_data.client_name} already exists")
            await self.remove_client(client_data.client_name)

        # Инициализация клиента
        client = client_data
        self.clients[client.client_name] = client

        try:
            # Создание объектов бота и диспетчера
            client.bot = Bot(token=client.token)
            client.dp = Dispatcher(
                storage=self.storage,
                fsm_strategy=self.fsm_strategy
            )
            client.dp.message.middleware(UserThrottlingMiddleware(limit=2.0))

            # Настройка роутера
            router = client.router
            client.dp.include_router(router)

            # Создание и запуск задачи для поллинга
            client.task = asyncio.create_task(
                self._execute_polling_safely(
                    client.dp, client.bot, client.client_name),
                name=f"bot_{client.client_name}"
            )

        except Exception as e:
            # Безопасная очистка при ошибке инициализации
            await self.remove_client(client.client_name)
            raise RuntimeError(
                f"Failed to start client {client.client_name}: {str(e)}") from e

    async def _execute_polling_safely(self, dp: Dispatcher, bot: Bot, client_name: str) -> None:
        """Запуск поллинга с обработкой исключений"""
        try:
            await dp.start_polling(bot)
        except asyncio.CancelledError:
            # Нормальная остановка по запросу
            pass
        except Exception as e:
            # Логирование критических ошибок поллинга
            log.error(f"Critical polling error for {client_name}: {str(e)}")
            raise

    async def remove_client(self, client_name: str) -> None:
        """Безопасная остановка и удаление клиента с очисткой ресурсов"""
        if not (client := self.clients.get(client_name)):
            return  # Клиент не существует, ничего не делаем

        # Остановка компонентов клиента
        if client.bot:
            await client.bot.session.close()
        if client.dp:
            try:
                await client.dp.stop_polling()
            except RuntimeError as e:
                # Игнорируем ошибку "Polling is not started"
                if "Polling is not started" not in str(e):
                    log.error(f"Error stopping polling for {client_name}: {str(e)}")

        # Отмена асинхронной задачи
        if client.task and not client.task.done():
            client.task.cancel()
            try:
                await client.task
            except asyncio.CancelledError:
                pass

        # Удаление клиента из словаря
        self.clients.pop(client_name)

    async def stop_all(self) -> None:
        await asyncio.gather(*(self.remove_client(client_name) for client_name in list(self.clients.keys())))
