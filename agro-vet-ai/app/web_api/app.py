from fastapi import FastAPI
from app.web_api.router_api import router as api_router
from app.web_api.router_lab import router as lab_router
from app.web_api.router_openai import openai_router


def create_app():
    """
    Создаёт и настраивает экземпляр FastAPI-приложения.

    :return: Настроенное FastAPI-приложение.
    """
    app = FastAPI()

    # Подключаем наши внутренние роуты
    app.include_router(api_router)

    # Подключаем роутер для обработки лабораторных результатов
    app.include_router(lab_router)

    # Подключаем роутер, совместимый с OpenAI API
    app.include_router(openai_router, prefix="")

    return app