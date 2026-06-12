FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/common app/common
COPY app/database app/database
COPY app/redis_queue app/redis_queue
COPY config config
COPY workers/common_tasks/worker.py .env .

RUN mkdir -p /app/storage && \
    groupadd -r appuser && \
    useradd -r -m -d /home/appuser -g appuser appuser && \
    chown -R appuser:appuser /app /home/appuser && \
    chmod 755 /app/storage

USER appuser

CMD ["python", "-m", "worker"]