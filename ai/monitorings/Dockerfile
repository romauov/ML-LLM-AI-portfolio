FROM python:3.11-slim

WORKDIR /app

COPY requirements-app-worker.txt .

RUN pip install --no-cache-dir -r requirements-app-worker.txt

COPY app ./app
COPY .env .

RUN python -c "import nltk; nltk.download('stopwords')"
RUN python -c "import nltk; nltk.download('punkt_tab')"
