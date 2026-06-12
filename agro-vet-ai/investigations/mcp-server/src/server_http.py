"""HTTP транспорт для MCP сервера VetRetro.

Запускает MCP сервер через HTTP/SSE для удаленного доступа.
"""

from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route, Mount
from mcp.server.sse import SseServerTransport

from .server import app as mcp_app
from .config import settings

import logging

logger = logging.getLogger(__name__)


# Создание SSE транспорта
sse = SseServerTransport("/messages/")


# Lifespan для управления ресурсами
@asynccontextmanager
async def lifespan(app: Starlette):
    """Управление жизненным циклом приложения."""
    logger.info("Запуск HTTP MCP сервера...")
    logger.info(f"База данных: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    logger.info(f"Модель эмбеддингов: {settings.embedding_model}")
    yield
    logger.info("Остановка HTTP MCP сервера...")


async def handle_sse(request: Request):
    """
    Обработка MCP запросов через Server-Sent Events.

    Этот эндпоинт используется для двунаправленной коммуникации
    между клиентом и MCP сервером через SSE.
    """
    logger.info(f"Новое SSE соединение от {request.client.host}")

    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_app.run(
            streams[0], streams[1], mcp_app.create_initialization_options()
        )

    # Return empty response to avoid NoneType error
    return Response()


async def handle_root(request: Request):
    """Корневой эндпоинт с информацией о сервере."""
    from starlette.responses import JSONResponse
    return JSONResponse({
        "name": "VetRetro MCP Server",
        "version": "1.0.0",
        "protocol": "MCP via HTTP/SSE",
        "endpoints": {
            "sse": "/sse",
            "messages": "/messages/",
            "health": "/health"
        }
    })


async def handle_health(request: Request):
    """Health check эндпоинт для мониторинга."""
    from starlette.responses import JSONResponse
    return JSONResponse({
        "status": "healthy",
        "service": "VetRetro MCP Server"
    })


# Создание Starlette приложения с маршрутами
app = Starlette(
    routes=[
        Route("/", endpoint=handle_root, methods=["GET"]),
        Route("/health", endpoint=handle_health, methods=["GET"]),
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
    ],
    lifespan=lifespan
)


def run_http_server(host: str = "0.0.0.0", port: int = 8765):
    """
    Запуск HTTP сервера.

    Args:
        host: Хост для прослушивания (по умолчанию 0.0.0.0)
        port: Порт для прослушивания (по умолчанию 8765)
    """
    import uvicorn

    uvicorn.run(
        "src.server_http:app",
        host=host,
        port=port,
        log_level=settings.log_level.lower(),
        reload=False
    )


if __name__ == "__main__":
    run_http_server()
