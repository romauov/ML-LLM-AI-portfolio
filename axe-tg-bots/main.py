import asyncio
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.router import bot_manager, router
from utils.get_clients_from_db import get_client_data_from_db
from utils.logger import logger as log

app = FastAPI(
    title="Telegram Bot Manager API",
    description="API для управления Telegram ботами Axe"
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации Pydantic"""
    error_details = exc.errors()
    log.error(f"Validation error for request {request.method} {request.url}: {error_details}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_details},
    )


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    log.info("Bot Manager API starting up...")
    try:
        clients = get_client_data_from_db()
        tasks = []
        for client in clients:
            task = bot_manager.add_and_start_client(client)
            tasks.append(task)
            log.info(f"Starting bot for client: {client.client_name}")

        # Параллельный запуск всех ботов
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Обработка результатов запуска
        for client, result in zip(clients, results):
            if isinstance(result, Exception):
                log.error(
                    f"Failed to start bot '{client.client_name}': {result}")
            else:
                log.info(f"Bot '{client.client_name}' started successfully")
    except Exception as e:
        log.error("Failed to start bots from DB")
        log.error(e)


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка ресурсов при остановке приложения"""
    log.info("Shutting down Bot Manager...")
    await bot_manager.stop_all()
    log.info("All bots stopped successfully")

# Регистрируем основной роутер в приложении
app.include_router(router)
