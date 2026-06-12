# VetRetro MCP Server

MCP (Model Context Protocol) сервер для доступа к ветеринарной базе знаний через семантический поиск и навигацию по документам.

> 📖 **Дополнительная информация о MCP**: Подробная документация по Model Context Protocol и интеграции с Claude доступна по ссылке: [https://docs.claude.com/en/docs/claude-code/mcp](https://docs.claude.com/en/docs/claude-code/mcp)

## Возможности

Сервер предоставляет 5 инструментов для работы с базой знаний и документами:

### 1. `vet_search` - Семантический поиск

Поиск релевантной информации по запросу на естественном языке с расширенной статистикой.

**Параметры:**
- `query` (обязательный) - поисковый запрос
- `limit` (опционально, по умолчанию 5) - количество результатов (1-20)
- `offset` (опционально, по умолчанию 0) - пропуск результатов для пагинации
- `source_filter` (опционально) - фильтр по конкретному источнику

**Возвращает:**
- Статистику поиска (всего найдено, распределение по источникам, диапазон схожести)
- Фрагменты страниц с информацией об источнике, главе и ключевых словах

**Пример:**
```json
{
  "query": "antibiotic therapy swine E.coli",
  "limit": 5,
  "offset": 0
}
```

### 2. `vet_sources` - Список источников

Получение списка всех доступных источников с описаниями.

**Параметры:** нет

**Возвращает:**
- Название источника
- Описание
- Диапазон страниц
- Количество глав

### 3. `source_info` - Информация об источнике

Детальная информация об источнике с оглавлением.

**Параметры:**
- `source_document` (обязательный) - название источника

**Возвращает:**
- Диапазон страниц
- Список глав с диапазонами страниц

### 4. `get_pages` - Получение страниц

Получение контента с конкретных страниц источника.

**Параметры:**
- `source_document` (обязательный) - название источника
- `page_start` (обязательный) - начальная страница
- `page_end` (опционально) - конечная страница

**Пример:**
```json
{
  "source_document": "Болезни свиней",
  "page_start": 10,
  "page_end": 15
}
```

### 5. `extract_document` - Извлечение текста из документов

Извлечение текста из PDF и DOCX файлов с использованием VseGPT API.

**Параметры:**
- `file_path` (обязательный) - абсолютный путь к файлу

**Поддерживаемые форматы:**
- **PDF** - с OCR и извлечением изображений (таблицы, графики)
- **DOCX** - извлечение текста

**Автоматически сохраняет:**
- Каждую страницу PDF в отдельный MD файл: `page_001.md`, `page_002.md`, ...
- Извлеченные изображения: `img-0.jpeg`, `img-1.jpeg`, ...
- DOCX контент в один файл: `content.md`
- Результаты в: `extracted_documents/<имя_файла>/`

**Возвращает:**
- Краткое содержимое (первые 1000 символов)
- Пути к сохраненным файлам
- Метаданные (модель, размер файла, количество страниц)

**Пример:**
```json
{
  "file_path": "/home/vet/lab_results.pdf"
}
```

**Результат:**
```
extracted_documents/lab_results/
  ├── page_001.md (результаты анализа)
  ├── page_002.md (расшифровка)
  └── img-0.jpeg (таблица с данными)
```

**Использование в расследовании:**
1. Извлечь текст из PDF с лабораторными результатами
2. Прочитать сохраненные страницы через Read tool
3. Сохранить данные в `05_lab_results.md`
4. Провести поиск в базе знаний по выявленным патогенам

## Установка

### 1. Установка зависимостей

```bash
cd mcp-server
python3 -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
```

### 2. Настройка конфигурации

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите ваши параметры:

```env
# PostgreSQL Database
DB_HOST=10.0.3.123
DB_PORT=5432
DB_NAME=vetbot
DB_USER=vetbot
DB_PASSWORD=vetbot

# OpenAI API для эмбеддингов (VseGPT)
OPENAI_API_KEY=sk-or-vv-ваш-ключ
OPENAI_API_BASE=https://api.vsegpt.ru/v1

# Параметры поиска
# Примечание: EMBEDDING_MODEL фиксирована в коде (text-embedding-3-small)
# Примечание: DEFAULT_LIMIT (количество результатов по умолчанию = 5) фиксировано в коде
SIMILARITY_THRESHOLD=0.6
```

## Запуск

Сервер поддерживает два варианта транспорта:

### 1. STDIO Transport (для Claude Desktop / Qwen Code)

Используется для локальной интеграции с LLM-клиентами через стандартные потоки ввода/вывода.

```bash
cd mcp-server
source venv/bin/activate  # или venv\Scripts\activate на Windows
python3 run_stdio.py
```

### 2. HTTP/SSE Transport (для удаленного доступа)

Используется для удаленного доступа к MCP серверу через HTTP и Server-Sent Events.

```bash
cd mcp-server
source venv/bin/activate
python3 run_http.py

# Или напрямую с uvicorn
uvicorn src.server_http:app --host 0.0.0.0 --port 8765
```

Сервер будет доступен по адресу `http://localhost:8765`:
- `GET /` - информация о сервере
- `GET /sse` - SSE endpoint для клиентов
- `POST /messages/` - отправка сообщений серверу

Подробности в [docs/transports.md](docs/transports.md).

### 3. Docker (рекомендуется для продакшена)

Docker контейнеризация упрощает развертывание и обеспечивает изоляцию окружения.

#### Сборка образа

```bash
cd mcp-server
docker build -t vetretro-mcp-server .
```

#### Запуск HTTP сервера через Docker Compose

```bash
# Запуск в фоновом режиме
docker-compose up -d mcp-server-http

# Просмотр логов
docker-compose logs -f mcp-server-http

# Остановка
docker-compose down
```

Сервер будет доступен на `http://localhost:8765`

#### Запуск через docker run

**HTTP режим:**
```bash
docker run -d \
  --name vetretro-mcp-http \
  -p 8765:8765 \
  --env-file .env \
  vetretro-mcp-server
```

**STDIO режим (для локального использования):**
```bash
docker run -it --rm \
  --name vetretro-mcp-stdio \
  --env-file .env \
  vetretro-mcp-server python run_stdio.py
```

**STDIO режим через docker-compose:**
```bash
docker-compose run --rm mcp-server-stdio
```

#### Health Check

Проверка работоспособности HTTP сервера:
```bash
curl http://localhost:8765/health
```

#### Остановка и удаление

```bash
# Остановка контейнера
docker stop vetretro-mcp-http

# Удаление контейнера
docker rm vetretro-mcp-http

# Или через docker-compose
docker-compose down
```

### Тестирование

Запуск тестов:

```bash
source venv/bin/activate

# Тесты базы знаний
python tests/test_kb.py

# Тесты MCP инструментов
python tests/test_mcp_tools.py

# Просмотр содержимого страницы
python scripts/show_page.py
```

## Интеграция с Claude Desktop

### Настройка

Добавьте конфигурацию в файл:
- **Linux**: `~/.config/Claude/claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Пример конфигурации также доступен в файле `claude_desktop_config_example.json`.

### Вариант 1: STDIO транспорт (рекомендуется для локального использования)

```json
{
  "mcpServers": {
    "vetretro": {
      "command": "/абсолютный/путь/к/VetRetro/mcp-server/venv/bin/python3",
      "args": ["run_stdio.py"],
      "cwd": "/абсолютный/путь/к/VetRetro/mcp-server",
      "env": {
        "OPENAI_API_KEY": "sk-or-vv-ваш-ключ",
        "OPENAI_API_BASE": "https://api.vsegpt.ru/v1",
        "DB_HOST": "10.0.3.123",
        "DB_PORT": "5432",
        "DB_NAME": "vetbot",
        "DB_USER": "vetbot",
        "DB_PASSWORD": "vetbot",
        "SIMILARITY_THRESHOLD": "0.6",
        "LOG_LEVEL": "INFO",
        "http_proxy": "",
        "https_proxy": "",
        "HTTP_PROXY": "",
        "HTTPS_PROXY": "",
        "all_proxy": "",
        "ALL_PROXY": ""
      }
    }
  }
}
```

**Важно:**
- Используйте абсолютные пути к директории `mcp-server` и Python из venv
- На Windows используйте обратные слэши в пути: `C:\\Users\\...\\VetRetro\\mcp-server`
- Обязательно очистите прокси-переменные (установите в пустую строку `""`)
- Сервер автоматически удаляет прокси при запуске, но лучше указать явно в конфигурации

### Вариант 2: HTTP/SSE транспорт (рекомендуется для удаленного доступа)

Сначала запустите MCP сервер в HTTP режиме:
```bash
cd /абсолютный/путь/к/VetRetro/mcp-server
docker-compose up -d mcp-server-http
```

Затем добавьте конфигурацию:
```json
{
  "mcpServers": {
    "vetretro-http": {
      "url": "http://localhost:8765/sse"
    }
  }
}
```

Или для удаленного сервера:
```json
{
  "mcpServers": {
    "vetretro-http": {
      "url": "http://10.0.3.123:8765/sse"
    }
  }
}
```

**Преимущества HTTP режима:**
- ✅ Один сервер для нескольких клиентов (Claude Desktop, Qwen Code, Cursor)
- ✅ Удаленный доступ с других машин
- ✅ Проще управление через Docker
- ✅ Централизованные логи
- ✅ Не нужно настраивать venv на каждой машине

**Когда использовать:**
- STDIO: локальная разработка, один клиент, быстрый запуск
- HTTP: несколько клиентов, удаленный доступ, продакшен

### Проверка подключения

1. Перезапустите Claude Desktop
2. В новом чате инструменты `vet_search`, `vet_sources`, `source_info`, `get_pages` должны быть доступны
3. Попробуйте выполнить поиск: "Найди информацию о диарее поросят"

## База знаний

Сервер работает с PostgreSQL базой данных, содержащей:

**Источники:**
1. Antimicrobial Therapy in Veterinary Medicine, 5th Edition
2. Examination of pharmacokinetic/pharmacodynamic relationships (свиньи)
3. Practical guide to broiler health management
4. Болезни свиней

**Статистика:**
- Всего записей: 3,451 чанка
- Размерность эмбеддингов: 1536
- Модель: text-embedding-3-small (через VseGPT API)

## Архитектура

```
mcp-server/
├── src/
│   ├── config.py           # Конфигурация (pydantic-settings)
│   ├── embeddings.py       # Генерация эмбеддингов (OpenAI API)
│   ├── knowledge_base.py   # RAG поиск (PostgreSQL + pgvector)
│   ├── server.py           # Ядро MCP сервера с инструментами
│   └── server_http.py      # HTTP/SSE транспорт (Starlette)
├── run_stdio.py            # Запуск через STDIO (Claude Desktop)
├── run_http.py             # Запуск через HTTP/SSE (удаленный доступ)
├── tests/
│   ├── test_kb.py          # Тесты базы знаний
│   └── test_mcp_tools.py   # Тесты MCP инструментов
├── scripts/
│   └── show_page.py        # Утилита для просмотра страниц
├── docs/
│   └── transports.md       # Документация по транспортам
├── .env.example
├── requirements.txt
└── README.md
```

**Архитектура транспортов:**

```
src/server.py (ядро MCP с инструментами)
    ↓
    ├─→ run_stdio.py → stdio_server() → Claude Desktop/Qwen Code
    └─→ run_http.py → server_http.py → HTTP/SSE → Удаленные клиенты
```

Оба транспорта используют одну и ту же бизнес-логику из `src/server.py`.

## Troubleshooting

### Проблемы с прокси

Если возникают ошибки с прокси при работе с OpenAI API, убедитесь что прокси-переменные не установлены:

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
```

### Низкая релевантность результатов поиска

Если поиск не возвращает результаты:
1. Проверьте порог схожести `SIMILARITY_THRESHOLD` (по умолчанию 0.6)
   - Меньшее значение = строже (меньше результатов, выше релевантность)
   - Большее значение = мягче (больше результатов, ниже релевантность)
2. Попробуйте запросы на английском языке (больше контента в базе)
3. Используйте более конкретные термины
4. Модель эмбеддингов `text-embedding-3-small` фиксирована в коде

### Ошибки подключения к базе данных

Проверьте параметры подключения:
```bash
PGPASSWORD=vetbot psql -h 10.0.3.123 -U vetbot -d vetbot
```

## Разработка

### Добавление новых инструментов

1. Реализуйте функцию-обработчик в `src/server.py`
2. Добавьте описание инструмента в `list_tools()`
3. Добавьте вызов в `call_tool()`
4. Создайте тесты в `tests/test_mcp_tools.py`

### Форматирование кода

```bash
# Проверка
ruff check src/

# Форматирование
black src/
```

## Лицензия

Этот проект разработан для внутреннего использования в VetRetro.
