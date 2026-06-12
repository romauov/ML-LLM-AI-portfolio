# MCP Server Transports

VetRetro MCP сервер поддерживает два варианта транспорта:

## 1. STDIO Transport (для локального использования)

Используется для интеграции с Claude Desktop и Qwen Code через стандартные потоки ввода/вывода.

### Запуск:
```bash
python3 run_stdio.py
```

### Конфигурация для Claude Desktop:

Добавьте в `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) или
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "vetretro": {
      "command": "python3",
      "args": ["/path/to/mcp-server/run_stdio.py"],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Конфигурация для Qwen Code:

Похожая конфигурация в настройках Qwen Code.

## 2. HTTP/SSE Transport (для удаленного доступа)

Используется для удаленного доступа к MCP серверу через HTTP и Server-Sent Events.

### Запуск:
```bash
# Запуск на всех интерфейсах, порт 8000
python3 run_http.py

# Или с uvicorn напрямую
uvicorn src.server_http:app --host 0.0.0.0 --port 8000
```

### Endpoints:

- `GET /` - Информация о сервере
- `GET /sse` - SSE endpoint для получения сообщений от сервера
- `POST /messages/` - Endpoint для отправки сообщений серверу

### Клиент для HTTP/SSE:

```python
import httpx
from mcp.client.sse import sse_client

async with sse_client("http://localhost:8000/sse") as (read, write):
    # Используйте read и write потоки для коммуникации с сервером
    pass
```

## Архитектура

Оба транспорта используют одну и ту же бизнес-логику:

- `src/server.py` - Ядро MCP сервера с определениями инструментов (@app.list_tools, @app.call_tool)
- `run_stdio.py` - Запуск через stdio транспорт
- `src/server_http.py` - Запуск через HTTP/SSE транспорт

Это позволяет поддерживать единый код и тестировать функциональность независимо от транспорта.

## Зависимости

### Базовые (для обоих транспортов):
- mcp >= 0.9.0
- asyncpg
- pgvector
- openai
- pydantic, pydantic-settings

### Только для HTTP транспорта:
- fastapi >= 0.104.0
- uvicorn[standard] >= 0.24.0
- sse-starlette >= 1.8.0

Установка всех зависимостей:
```bash
pip install -r requirements.txt
```
