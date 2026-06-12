# Eval-тесты Agro-Vet AI

Качественная оценка ответов агентов: дифференциальная диагностика свиней и птиц,
вопросы к librarian и pharmacist. Каждый тест отправляет реальный запрос к API
и проверяет ответ через лемматизацию.

## Требования

```
pip install -r requirements.txt
pip install pytest pytest-xdist  # pytest-xdist нужен только для -n
```

Переменные окружения (`.env` или environment):

| Переменная              | Назначение                                  |
|-------------------------|---------------------------------------------|
| `API_KEY`               | Ключ доступа к API бота                     |
| `API_SERVICE_HOST_PORT` | Порт локального сервера (например, `8000`)  |
| `OPENROUTER_BASE_URL`   | Base URL для embeddings                     |
| `OPENROUTER_API_KEY`    | API-ключ для embeddings                     |
| `EMBEDDING_MODEL`       | Модель эмбеддингов (например, `emb-openai/text-embedding-3-small`) |

## Запуск

```bash
# Все тесты
python -m pytest tests/pytest/eval/ -v

# Конкретный класс
python -m pytest tests/pytest/eval/ -v -k TestSwineDiagnosis

# Конкретный тест
python -m pytest tests/pytest/eval/ -v -k test_prrs_symptoms

# Параллельно (N воркеров)
python -m pytest tests/pytest/eval/ -v -n 4

# Остановиться на первом падении
python -m pytest tests/pytest/eval/ -v -x

# Показать вывод (запросы/ответы) даже для упавших
python -m pytest tests/pytest/eval/ -v -s
```

## Тест-классы

| Класс                  | Тестов | Что проверяется                                      |
|------------------------|--------|------------------------------------------------------|
| `TestGeneralQuestions` | 1      | Общие возможности бота                               |
| `TestSwineDiagnosis`   | 5      | Дифф. диагностика болезней свиней по симптомам       |
| `TestAvianDiagnosis`   | 5      | Дифф. диагностика болезней птиц по симптомам         |
| `TestLibrarian`        | 5      | Ответы из базы знаний с указанием источника          |
| `TestPharmacist`       | 5      | Ответы по препаратам из БД с указанием источника     |

## Логи

После каждого прогона в `logs/<дата>/<время>.json` сохраняется JSON-массив с полями:
`test_group`, `test_case`, `query`, `agent_response`, `reference_answer`, `status`, `assertion_message`, `query_processing_duration`, `test_duration`.
