FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY /src .

# Запускаем main.py с аргументами
ENTRYPOINT ["python", "mcp_server_forecasting/main.py"]
