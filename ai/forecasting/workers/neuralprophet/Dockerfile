FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements-cuda.txt .

RUN pip install --no-cache-dir -r requirements-cuda.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app app
COPY worker.py .

RUN mkdir -p /app/storage && \
    groupadd -r appuser && \
    useradd -r -m -d /home/appuser -g appuser appuser && \
    chown -R appuser:appuser /app /home/appuser && \
    chmod 755 /app/storage

USER appuser

CMD ["python", "-m", "worker"]