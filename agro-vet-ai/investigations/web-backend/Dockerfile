FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости (если нужны)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY investigations/web-backend/requirements.txt ./

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY investigations/web-backend/app/ ./app/
COPY investigations/web-backend/pyproject.toml ./
# Note: utils directory is expected to be mounted via volume in docker-compose

# Копируем AGENTS.md файлы в рабочую директорию
COPY investigations/agent-workspace/ /agent-workspace/

# Создаем директорию для investigations и выдаем права пользователю
RUN mkdir -p /agent-workspace/investigations && \
    useradd -m -u 1000 backend && \
    chown -R backend:backend /app /agent-workspace

USER backend

# Открываем порт для HTTP транспорта
EXPOSE 8000

# Запускаем uvicorn сервер
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000"]