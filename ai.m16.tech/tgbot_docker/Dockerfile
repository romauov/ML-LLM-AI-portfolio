FROM python:3.11-slim

WORKDIR /app/tgbot_docker

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .
COPY funcs/ ./funcs

CMD ["python", "-m", "bot"]
