#!/usr/bin/env python3
"""Запуск MCP сервера через stdio для Claude Desktop/Qwen Code."""

import asyncio
import logging

from mcp.server.stdio import stdio_server

from src.server import app
from src.config import settings

logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска MCP сервера через stdio."""
    logger.info("Запуск VetRetro MCP сервера (stdio)...")
    logger.info(f"База данных: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    logger.info(f"Модель эмбеддингов: {settings.embedding_model}")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
