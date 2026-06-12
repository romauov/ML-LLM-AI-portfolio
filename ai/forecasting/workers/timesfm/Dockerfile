FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/storage && \
    groupadd -r appuser && \
    useradd -r -m -d /home/appuser -g appuser appuser && \
    chown -R appuser:appuser /app /home/appuser && \
    chmod 755 /app/storage

COPY app app
COPY worker.py .

USER appuser

CMD ["python", "-m", "worker"]
