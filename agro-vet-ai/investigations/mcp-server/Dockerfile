# Используем официальный образ Python 3.11
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости (если нужны)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY investigations/mcp-server/requirements.txt ./
COPY investigations/mcp-server/pyproject.toml ./

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY investigations/mcp-server/src/ ./src/
COPY investigations/mcp-server/run_http.py ./
COPY investigations/mcp-server/run_stdio.py ./
# Note: utils directory is expected to be mounted via volume in docker-compose

# Создаём непривилегированного пользователя для запуска приложения
RUN useradd -m -u 1000 mcp && \
    chown -R mcp:mcp /app

USER mcp

# Открываем порт для HTTP транспорта (если используется)
EXPOSE 8765

# По умолчанию запускаем HTTP сервер
# Для stdio режима нужно переопределить CMD при запуске контейнера
CMD ["python", "run_http.py"]
