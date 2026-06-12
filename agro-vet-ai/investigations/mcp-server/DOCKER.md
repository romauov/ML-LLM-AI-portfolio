# Docker Development & Deployment Guide

Это руководство описывает использование Docker для развертывания MCP сервера VetRetro.

## Быстрый старт

### 1. Сборка образа

```bash
cd mcp-server
docker build -t vetretro-mcp-server .
```

### 2. Запуск через Docker Compose (рекомендуется)

**HTTP режим (для удаленного доступа):**

```bash
# Запуск в фоновом режиме
docker-compose up -d mcp-server-http

# Просмотр логов
docker-compose logs -f mcp-server-http

# Остановка
docker-compose down
```

**STDIO режим (для локального использования с Claude Desktop/Qwen Code):**

```bash
# Запуск в интерактивном режиме
docker-compose run --rm mcp-server-stdio
```

### 3. Проверка работоспособности

```bash
# Health check
curl http://localhost:8765/health

# Информация о сервере
curl http://localhost:8765/
```

Ожидаемый ответ:
```json
{
    "name": "VetRetro MCP Server",
    "version": "1.0.0",
    "protocol": "MCP via HTTP/SSE",
    "endpoints": {
        "sse": "/sse",
        "messages": "/messages/",
        "health": "/health"
    }
}
```

## Альтернативный запуск (docker run)

### HTTP режим

```bash
docker run -d \
  --name vetretro-mcp-http \
  -p 8765:8765 \
  --env-file .env \
  vetretro-mcp-server
```

### STDIO режим

```bash
docker run -it --rm \
  --name vetretro-mcp-stdio \
  --env-file .env \
  vetretro-mcp-server python run_stdio.py
```

## Управление контейнерами

### Просмотр запущенных контейнеров

```bash
docker ps
```

### Просмотр логов

```bash
# Docker Compose
docker-compose logs -f mcp-server-http

# Docker run
docker logs -f vetretro-mcp-http
```

### Остановка контейнера

```bash
# Docker Compose
docker-compose down

# Docker run
docker stop vetretro-mcp-http
docker rm vetretro-mcp-http
```

### Перезапуск контейнера

```bash
# Docker Compose
docker-compose restart mcp-server-http

# Docker run
docker restart vetretro-mcp-http
```

## Конфигурация

### Переменные окружения

Все переменные окружения задаются в файле `.env`. Создайте его на основе `.env.example`:

```bash
cp .env.example .env
```

Основные переменные:

```env
# PostgreSQL Database
DB_HOST=10.0.3.123
DB_PORT=5432
DB_NAME=vetbot
DB_USER=vetbot
DB_PASSWORD=vetbot

# OpenAI API для эмбеддингов (VseGPT)
OPENAI_API_KEY=sk-or-vv-ваш-ключ
OPENAI_API_BASE=https://api.vsegpt.ru/v1

# Параметры поиска
SIMILARITY_THRESHOLD=0.6
LOG_LEVEL=INFO
```

### Порты

По умолчанию сервер слушает порт **8765**. Если нужно изменить:

**В docker-compose.yml:**
```yaml
ports:
  - "8888:8765"  # <внешний порт>:<порт внутри контейнера>
```

**В docker run:**
```bash
docker run -d -p 8888:8765 --env-file .env vetretro-mcp-server
```

## Архитектура контейнера

### Структура образа

- **Base Image:** `python:3.11-slim`
- **Рабочая директория:** `/app`
- **Пользователь:** `mcp` (UID 1000, непривилегированный)
- **Порт:** 8765
- **Health Check:** `GET /health` каждые 30 секунд

### Размер образа

```bash
docker images vetretro-mcp-server
```

Примерный размер: ~570 MB

### Многослойность

Образ оптимизирован для кэширования слоев:
1. Системные зависимости (gcc, postgresql-client)
2. Python зависимости (requirements.txt)
3. Исходный код (src/)
4. Скрипты запуска (run_http.py, run_stdio.py)

## Режимы транспорта

### HTTP/SSE Transport

Используется для удаленного доступа к MCP серверу через HTTP и Server-Sent Events.

**Endpoints:**
- `GET /` - информация о сервере
- `GET /health` - health check
- `GET /sse` - SSE endpoint для клиентов
- `POST /messages/` - отправка сообщений серверу

**Docker Compose сервис:** `mcp-server-http`

**Конфигурация Claude Desktop для HTTP режима:**

1. Запустите сервер:
```bash
docker-compose up -d mcp-server-http
```

2. Добавьте в `~/.config/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "vetretro-http": {
      "url": "http://localhost:8765/sse"
    }
  }
}
```

Для удаленного сервера:
```json
{
  "mcpServers": {
    "vetretro-http": {
      "url": "http://10.0.3.123:8765/sse"
    }
  }
}
```

**Преимущества:**
- ✅ Один сервер для нескольких клиентов
- ✅ Удаленный доступ
- ✅ Проще управление

### STDIO Transport

Используется для локальной интеграции с LLM-клиентами через стандартные потоки ввода/вывода.

**Docker Compose сервис:** `mcp-server-stdio` (профиль `stdio`, не запускается автоматически)

**Примечание:** Для STDIO с Claude Desktop рекомендуется использовать venv вместо Docker (проще и быстрее).

## Troubleshooting

### Контейнер не запускается

Проверьте логи:
```bash
docker-compose logs mcp-server-http
```

### Не работает подключение к базе данных

Убедитесь, что база данных доступна из контейнера:
```bash
docker-compose exec mcp-server-http psql -h 10.0.3.123 -U vetbot -d vetbot
```

### Ошибки с API ключами

Проверьте, что `.env` файл содержит корректные значения:
```bash
cat .env | grep OPENAI_API_KEY
```

### Порт уже занят

Если порт 8765 занят, измените маппинг портов:
```bash
docker-compose down
# Отредактируйте docker-compose.yml: "8888:8765"
docker-compose up -d mcp-server-http
```

### Пересборка образа

Если изменили код или зависимости:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d mcp-server-http
```

## Продакшен рекомендации

### 1. Используйте Docker Compose

Предпочтительнее для управления сервисами и зависимостями.

### 2. Настройте логирование

Используйте внешний log driver для сохранения логов:

```yaml
services:
  mcp-server-http:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 3. Ограничьте ресурсы

```yaml
services:
  mcp-server-http:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '1.0'
          memory: 512M
```

### 4. Используйте secrets для чувствительных данных

Вместо `.env` используйте Docker secrets для продакшена.

### 5. Настройте мониторинг

Health check уже настроен в `docker-compose.yml`:
- Проверка каждые 30 секунд
- Timeout: 10 секунд
- Retries: 3
- Start period: 40 секунд

## Очистка

### Удалить контейнеры и сеть

```bash
docker-compose down
```

### Удалить образ

```bash
docker rmi vetretro-mcp-server
```

### Полная очистка (включая volumes)

```bash
docker-compose down -v
docker system prune -a
```

## Дополнительные ресурсы

- [Главный README](README.md) - Общая документация проекта
- [MCP Documentation](https://docs.claude.com/en/docs/claude-code/mcp) - Документация по Model Context Protocol
- [Docker Compose Documentation](https://docs.docker.com/compose/) - Документация Docker Compose
