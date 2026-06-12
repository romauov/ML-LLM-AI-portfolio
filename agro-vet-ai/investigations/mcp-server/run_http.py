#!/usr/bin/env python3
"""Запуск MCP сервера через HTTP/SSE для удаленного доступа."""

from src.server_http import run_http_server

if __name__ == "__main__":
    # Запуск на всех интерфейсах, порт 8765
    run_http_server(host="0.0.0.0", port=8765)
