# VetRetro Investigations Web Backend API

Специализированный backend для ветеринарных расследований, работающий на порту 8001.

## 🔍 Общие API Endpoints

### GET `/`
- **Назначение**: Проверка работоспособности сервиса VetRetro
- **Ответ**: Статус сервиса в формате JSON

```bash
curl http://localhost:8001/ \
  -H "Authorization: Bearer $API_KEY"
```

### GET `/hello`
- **Назначение**: Тестирование соединения с LLM
- **Ответ**: Сообщение о подключении к LLM с ответом модели

```bash
curl http://localhost:8001/hello \
  -H "Authorization: Bearer $API_KEY"
```

### GET `/mcp/test`
- **Назначение**: Тестирование соединения с MCP сервером
- **Ответ**: Статус подключения к MCP и список доступных инструментов

```bash
curl http://localhost:8001/mcp/test \
  -H "Authorization: Bearer $API_KEY"
```

### GET `/mcp/search`
- **Назначение**: Тестирование ветеринарного поиска через MCP
- **Параметры**:
  - `query` (string): Поисковый запрос
- **Ответ**: Результаты ветеринарного поиска

```bash
curl "http://localhost:8001/mcp/search?query=E.coli diarrhea piglets" \
  -H "Authorization: Bearer $API_KEY"
```

## 🤖 OpenAI-совместимые Endpoints

### GET `/v1/models`
- **Назначение**: Получение списка доступных моделей для расследований
- **Ответ**: Список доступных моделей для ветеринарных расследований

```bash
curl http://localhost:8001/v1/models \
  -H "Authorization: Bearer $API_KEY"
```

запрос должен возвращать модели для расследований: `investigations-swine` и `investigations-poultry`.

### POST `/v1/chat/completions`
- **Назначение**: Основной эндпоинт для ветеринарных расследований
- **Функция**: Обработка запросов через AI-агента с поддержкой потоковой передачи
- **Параметры**:
  - `model` (string): Модель для использования (investigations-swine или investigations-poultry)
  - `messages` (array): История чата в формате OpenAI
  - `stream` (boolean, optional): Включить потоковую передачу ответа
- **Ответ**: Ответ AI-ассистента в формате OpenAI API

#### Пример запроса без потоковой передачи:
```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer $API_KEY' \
  -d '{
    "model": "investigations-swine",
    "messages": [
      {"role": "user", "content": "Привет"}
    ],
    "stream": false
  }'
```

#### Пример потоковой передачи (stream=true):
При первом запросе в чат система автоматически создает новое расследование и возвращает специальное системное сообщение с информацией о расследовании и используемой модели:

```
data: {"id":"chatcmpl-3bf7dbecca5c489da6a5987f","object":"chat.completion.chunk","created":1765446994,"model":"investigations-swine","choices":[{"index":0,"delta":{"content":"**Investigation ID:** `inv_fc6d75`\n**Model:** `minimax/minimax-m2`\n\n"},"finish_reason":null}]}

data: {"id":"chatcmpl-3bf7dbecca5c489da6a5987f","object":"chat.completion.chunk","created":1765446994,"model":"investigations-swine","choices":[{"index":0,"delta":{"content":"Здравствуйте!"},"finish_reason":null}]}

...

data: {"id":"chatcmpl-3bf7dbecca5c489da6a5987f","object":"chat.completion.chunk","created":1765446994,"model":"investigations-swine","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

При потоковой передаче используется протокол Server-Sent Events (SSE):
- Каждое сообщение передается в формате SSE с префиксом "data:"
- ID запроса ("chatcmpl-3bf7dbecca5c489da6a5987f") используется для идентификации конкретного вызова API
- Первым сообщением идет системная информация с ID расследования и моделью ИИ
- Затем последовательно передаются фрагменты ответа (chunks)
- Каждый фрагмент содержит часть текста в поле "delta"
- Последним передается сообщение с finish_reason="stop"
- Завершает поток сообщение [DONE]

Пример запроса с потоковой передачей:
```bash
curl -X POST http://localhost:8001/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer $API_KEY' \
  -d '{
    "model": "investigations-swine",
    "messages": [
      {"role": "user", "content": "Привет"}
    ],
    "stream": true
  }'
```

## 🕵️ Endpoints управления расследованиями

### POST `/api/investigations/create`
- **Назначение**: Создание нового ветеринарного расследования
- **Функция**: Создает директорию и начальные файлы для нового расследования
- **Параметры**:
  - `farm_name` (string): Название фермы
  - `problem_type` (string): Тип проблемы (neonatal_diarrhea, respiratory и др.)
  - `description` (string, optional): Описание инцидента
- **Ответ**: Информация о созданном расследовании

```bash
curl -X POST http://localhost:8001/api/investigations/create \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer $API_KEY' \
  -d '{
    "farm_name": "Example Farm",
    "problem_type": "neonatal_diarrhea",
    "description": "Initial description of the issue"
  }'
```

### GET `/api/investigations/list`
- **Назначение**: Получение списка всех ветеринарных расследований
- **Ответ**: Массив информации о всех расследованиях

```bash
curl http://localhost:8001/api/investigations/list \
  -H "Authorization: Bearer $API_KEY"
```

### GET `/api/investigations/{investigation_id}`
- **Назначение**: Получение информации о конкретном расследовании
- **Параметры**:
  - `investigation_id` (string): ID расследования
- **Ответ**: Информация о расследовании

```bash
curl http://localhost:8001/api/investigations/inv_a3f8b2 \
  -H "Authorization: Bearer $API_KEY"
```

### GET `/api/investigations/{investigation_id}/files`
- **Назначение**: Получение списка файлов в расследовании
- **Параметры**:
  - `investigation_id` (string): ID расследования
- **Ответ**: Список файлов в расследовании

```bash
curl http://localhost:8001/api/investigations/inv_a3f8b2/files \
  -H "Authorization: Bearer $API_KEY"
```

### GET `/api/investigations/{investigation_id}/files/{file_name}`
- **Назначение**: Получение содержимого файла в расследовании
- **Параметры**:
  - `investigation_id` (string): ID расследования
  - `file_name` (string): Имя файла
- **Ответ**: Содержимое файла расследования

```bash
curl http://localhost:8001/api/investigations/inv_a3f8b2/files/00_incident.md \
  -H "Authorization: Bearer $API_KEY"
```

### POST `/api/investigations/{investigation_id}/files`
- **Назначение**: Обновление или создание файла в расследовании
- **Функция**: Записывает содержимое в указанный файл расследования
- **Параметры**:
  - `investigation_id` (string): ID расследования
  - `file_name` (string): Имя файла
  - `content` (string): Новое содержимое файла
- **Ответ**: Статус операции

```bash
curl -X POST http://localhost:8001/api/investigations/inv_a3f8b2/files \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer $API_KEY' \
  -d '{
    "file_name": "00_incident.md",
    "content": "Updated content for incident file"
  }'
```

### DELETE `/api/investigations/{investigation_id}`
- **Назначение**: Удаление расследования
- **Параметры**:
  - `investigation_id` (string): ID расследования для удаления
- **Ответ**: Статус операции удаления

```bash
curl -X DELETE http://localhost:8001/api/investigations/inv_a3f8b2 \
  -H "Authorization: Bearer $API_KEY"
```