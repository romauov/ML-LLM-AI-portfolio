# TODO: VetRetro - Веб-интерфейс (MVP v2)

**📋 Техническое задание:** [docs/ТЗ-Web.md](docs/ТЗ-Web.md)
_(полное описание архитектуры, технологий и справочных материалов)_

**Подход:** Langchain + LangServe + Backend Tools (2 сервера, 71 задача, 3-5 дней)

---

## Этап 1: Базовая структура + Hello World

**Результат:** Запускается пустой FastAPI сервер с подключением к OpenRouter.

### 1.1. Структура проекта
- [x] Создать директорию `web-backend/`
- [x] Создать `pyproject.toml` с зависимостями
  - fastapi, uvicorn, pydantic, python-dotenv
  - langchain, langchain-openai, langserve
  - mcp, httpx (для подключения к vetretro MCP)
- [x] Создать `requirements.txt`
- [x] Создать структуру директорий:
  - `app/` - основное приложение
  - `app/agents/` - Langchain агенты и промпты
  - `app/tools/` - Langchain Tools (MCP обертки + файловые инструменты)
  - `app/api/` - Custom API endpoints (investigations)
  - `app/services/` - Утилиты (MCP клиент, investigation manager)
  - `app/models/` - Pydantic модели
  - `tests/` - тесты
- [x] Создать `.env.example` с шаблоном конфигурации
- [x] Создать `README.md`

### 1.2. Конфигурация и простой Hello World
- [x] Создать `app/config.py`
  - OpenRouter API key и base URL
  - Путь к agent-workspace/investigations
  - Настройки CORS
- [x] Создать `.env` с реальными ключами
- [x] Создать `app/main.py` (минимальный)
  - Инициализация FastAPI
  - Health check endpoint (/)
  - Тестовый endpoint /hello с вызовом OpenRouter
  - Очистка прокси-переменных для корректной работы OpenAI клиента
- [x] Запустить и проверить: `uvicorn app.main:app --reload`
- [x] Убедиться что OpenRouter отвечает

**✅ Чекпоинт:** FastAPI работает, OpenRouter подключен.

---

## Этап 2: Investigation Manager (работа с файлами)

**Результат:** Можно создавать расследования и работать с файлами через Python API.

### 2.1. Pydantic модели
- [x] Создать `app/models/investigation.py`
  - Investigation (id, farm_name, status, created_at)
  - InvestigationCreate (farm_name, animal_type, problem_type, description)
  - InvestigationFile (filename, content, size)
  - InvestigationListItem (облегченная модель для списка)
  - InvestigationStatus (enum)

### 2.2. Investigation Manager (файловые операции)
- [x] Посмотреть как реализованы инструменты для работы с файлами в qwen-code (см. ТЗ)
- [x] Создать `app/services/investigation_manager.py`
  - Класс InvestigationManager для работы с файлами расследований
  - Метод create_investigation(farm_name, animal_type, problem_type, description)
    - Создает папку `YYYYMMDD_farm-name_problem/`
    - Создает базовые файлы (00_incident.md, 01_group_card.md, STATUS.md)
  - Метод list_investigations() - список всех расследований
  - Метод get_investigation(investigation_id) - получение деталей
  - Метод list_files(investigation_id) - список файлов расследования
  - Метод read_file(investigation_id, filename) - чтение файла
  - Метод write_file(investigation_id, filename, content) - запись файла
  - Метод append_to_file(investigation_id, filename, content) - добавление
  - Метод update_file_section(investigation_id, filename, section, content) - обновление секции
  - Валидация путей (только в пределах agent-workspace)
  - Проверка безопасности (path traversal prevention)
  - Санитизация имен ферм
- [x] Протестировать Investigation Manager в Python REPL
  - Создать тестовое расследование
  - Записать и прочитать файл
  - Проверить валидацию путей

**✅ Чекпоинт:** Investigation Manager работает, файлы создаются корректно.

---

## Этап 3: Подключение MCP vetretro (база знаний)

**Результат:** Можно делать семантический поиск по ветеринарной базе знаний.

### 3.1. MCP клиент для vetretro
- [x] Создать `app/services/mcp_client.py`
  - Класс MCPClient для подключения к vetretro MCP через SSE
  - Метод connect(url) - подключение к серверу
  - Метод list_tools() - получение списка инструментов MCP
  - Метод call_tool(name, arguments) - вызов инструмента
  - Обработка ошибок и переподключение
  - Класс VetRetroMCPClient с удобными методами (vet_search, vet_sources, source_info, get_pages, extract_document)
- [x] Создать экземпляр клиента для vetretro
- [x] Реализовать инициализацию при старте приложения (в main.py)
  - Добавлен lifespan context manager
  - Глобальный mcp_client инстанс
  - Логирование запуска
- [x] Запустить vetretro MCP сервер: `cd mcp-server && source venv/bin/activate && python run_http.py`
- [x] Протестировать подключение и вызов vet_search через HTTP API
  - GET /mcp/test - проверка подключения и список инструментов
  - GET /mcp/search?query=... - тест поиска по базе знаний

**✅ Чекпоинт:** MCP клиент подключен к vetretro, поиск работает.

---

## Этап 4: Langchain Tools (обертки для инструментов)

**Результат:** Все инструменты доступны как Langchain Tools (MCP + файловые + todo).

### 4.1. MCP Tools (база знаний vetretro)
- [ ] Создать `app/tools/mcp_tools.py`
  - Функция create_mcp_tools(mcp_client) - обертка MCP инструментов в Langchain Tools
  - VetSearchTool - семантический поиск (vet_search)
  - VetSourcesTool - список источников (vet_sources)
  - SourceInfoTool - информация об источнике (source_info)
  - GetPagesTool - извлечение страниц (get_pages)

### 4.2. Файловые инструменты
- [ ] **ВАЖНО:** Изучить оригинальные описания инструментов из qwen-code (docs/qwen-code-tools.json)
  - Описание инструментов критически важно для правильной работы агента
  - Адаптировать description, examples для ветеринарного контекста
  - Проверить формат параметров и их описания
- [ ] Создать `app/tools/investigation_tools.py`
  - CreateInvestigationTool - создание нового расследования
  - ListInvestigationsTool - список всех расследований
  - ListFilesTool - список файлов расследования
  - ReadFileTool - чтение файла расследования
  - WriteFileTool - запись файла
  - AppendToFileTool - добавление в конец файла
  - UpdateFileSectionTool - обновление секции markdown
  - Все инструменты используют InvestigationManager
  - Все инструменты наследуют BaseTool из Langchain

### 4.3. Todo инструмент
- [ ] Создать `app/tools/todo_tool.py`
  - TodoWriteTool - управление задачами расследования
  - Формат совместимый с Qwen Code
  - Сохранение в память или файл
- [ ] Протестировать все Tools в Python REPL
  - Создать экземпляры всех tools
  - Вызвать каждый tool с тестовыми параметрами
  - Проверить что возвращают корректные результаты

**✅ Чекпоинт:** Все Tools работают, готовы к использованию агентом.

---

## Этап 5: Ветеринарный агент (промпт + AgentExecutor)

**Результат:** Агент работает локально через Python, может вызывать все инструменты.

### 5.1. Системный промпт
- [x] Создать `app/agents/prompts.py`
  - ChatPromptTemplate для ветеринарного агента
  - Адаптация промпта из Qwen Code для ветеринарного домена
  - Базовые принципы: Evidence-Based, Source Citations, Iterative Investigation
  - Переменные: investigation_id, workspace_path, chat_history, input, agent_scratchpad
  - Примеры использования для ветеринарных расследований
- [x] Опционально: загрузка AGENTS.md из agent-workspace

### 5.2. AgentExecutor
- [x] Создать `app/agents/vet_agent.py`
  - Инициализация ChatOpenAI с OpenRouter (base_url, api_key, model)
  - Сборка всех tools (MCP tools + investigation tools + todo tool)
  - Создание агента через create_openai_tools_agent(llm, tools, prompt)
  - Создание AgentExecutor с max_iterations и return_intermediate_steps
  - Функция get_vet_agent_executor() - возвращает готовый AgentExecutor
- [x] Протестировать агента в Python REPL
  - Создать тестовое расследование
  - Задать вопрос агенту о диарее у поросят
  - Проверить что агент вызывает vet_search
  - Проверить что агент создает файлы

**✅ Чекпоинт:** Агент работает локально, вызывает инструменты, создает файлы.

---

## Этап 6: LangServe API (веб-доступ к агенту)

**Результат:** Агент доступен через OpenAI-совместимый API, можно подключить Open WebUI.

### 6.1. API endpoints
- [x] Создать `app/api/investigations.py`
  - GET /api/investigations/list - список расследований
  - POST /api/investigations/create - создание нового
  - GET /api/investigations/{id} - детали расследования
  - GET /api/investigations/{id}/files/{filename} - содержимое файла
  - POST /api/investigations/{id}/files - обновление файла
  - DELETE /api/investigations/{id} - удаление расследования
  - Использование InvestigationManager для всех операций
- [x] Создать `app/api/chat.py` с OpenAI-compatible endpoints
  - POST /v1/chat/completions - основной endpoint (streaming + non-streaming)
  - GET /v1/models - список доступных моделей

**Примечание:** Реализовано без LangServe, напрямую через FastAPI для полного контроля над форматом.

### 6.2. OpenAI-compatible Chat API
- [x] Реализовать POST /v1/chat/completions
  - Поддержка streaming (SSE) и non-streaming режимов
  - OpenAI-совместимый формат запросов/ответов
  - Интеграция с AgentExecutor через astream_events
  - Поддержка investigation_id для контекстных расследований
- [x] Обновить `app/main.py`
  - Инициализация InvestigationManager в lifespan
  - Регистрация chat_router и investigations_router
  - Сохранение в app.state для доступа из endpoints
- [x] Создать test_api.sh для тестирования
- [x] Протестировать через curl
  - POST /v1/chat/completions (non-streaming) ✅
  - POST /v1/chat/completions (streaming) ✅
  - POST /api/investigations/create ✅
  - GET /api/investigations/list ✅
  - GET /api/investigations/{id}/files/{filename} ✅
  - POST /agent/stream с streaming
  - Проверить что работает tool calling

**✅ Чекпоинт:** API работает, агент доступен через HTTP, streaming функционирует.

---

## Этап 7: Интеграция с Open WebUI

**Результат:** Полноценный веб-интерфейс для работы с агентом.

### 7.1. Настройка Open WebUI
- [ ] Установить Open WebUI (Docker или pip)
- [ ] Настроить подключение к нашему backend
  - Base URL: http://localhost:8000
  - API Key: (если требуется)
- [ ] Проверить отображение в списке моделей

### 7.2. End-to-End тест через Open WebUI
- [ ] Инициировать новое расследование
- [ ] Предоставить описание инцидента
- [ ] Проверить создание файлов расследования
- [ ] Проверить работу поиска в базе знаний (vet_search)
- [ ] Предоставить данные вскрытия
- [ ] Проверить обновление гипотез
- [ ] Предоставить лабораторные данные
- [ ] Проверить создание финального отчета
- [ ] Проверить все файлы в investigations/

### 7.3. Финальная проверка
- [ ] Streaming работает корректно (сообщения приходят постепенно)
- [ ] Function calling работает (агент вызывает инструменты)
- [ ] Investigation tools работают (create_investigation, read_file, write_file, etc.)
- [ ] MCP-инструменты работают (vet_search, vet_sources, get_pages, etc.)
- [ ] Todo list отображается и обновляется
- [ ] Файлы создаются с правильной структурой
- [ ] Агент следует системному промпту


- [ ] LLM_MODEL: str = "qwen/qwen3-next-80b-a3b-instruct" - быстрая, толковая, но нужно решить проблему с вызовом инструментов!

### Известные проблемы:
- [ ] **Множественные папки расследований создаются автоматически** (inv_20251118_XXXXXX_YYYYYY/)
  - Возможно, Open WebUI делает запросы для автодополнения/рекомендаций следующих запросов
  - Или есть другая причина спонтанных вызовов create_investigation
  - Нужно: добавить логирование всех входящих запросов, понять источник
  - Рассмотреть: флаг dry_run для проверочных запросов или кэширование

**✅ Чекпоинт:** MVP v2 полностью работает через веб-интерфейс!

---

## Этап 8: Документация

- [ ] Обновить главный README.md проекта
  - Добавить раздел "Веб-интерфейс"
  - Схема упрощенной архитектуры (User → Open WebUI → FastAPI Backend → vetretro MCP)
  - Инструкции по запуску (2 сервера вместо 3)
- [ ] Создать web-backend/README.md
  - Описание API endpoints
  - Описание всех Langchain Tools
  - Примеры запросов (curl)
  - Переменные окружения
  - Troubleshooting
- [ ] Создать docs/API.md
  - Полная документация OpenAI-совместимого API (через LangServe)
  - Дополнительные endpoints (/v1/investigations/*)
  - Примеры интеграции

---

## Этап 9: Advanced Features (опционально)

### 9.1. Механизм повторных запросов при ошибках провайдера
- [ ] Реализовать retry механизм для OpenRouter API вызовов
  - Exponential backoff с ограниченным количеством попыток (3-5 retries)
  - Обработка специфичных ошибок: "Provider returned error", timeout, rate limit
  - Логирование всех retry попыток
  - Настраиваемые параметры: max_retries, base_delay, max_delay
- [ ] Интегрировать в stream_agent_response() в app/api/chat.py
- [ ] Добавить конфигурацию в app/config.py
- [ ] Протестировать с намеренными ошибками

### 9.2. Механизм auto-continue
- [ ] Изучить реализацию в [QwenLM/qwen-code](https://github.com/QwenLM/qwen-code)
- [ ] Реализовать инструмент `respond_in_schema`
  - Parameters: reasoning (string), next_speaker (enum: "user" | "model")
- [ ] Добавить проверочное сообщение в агентный цикл
- [ ] Реализовать логику принятия решения (продолжить / вернуть пользователю)
- [ ] Добавить эвристики для очевидных случаев (опционально)
- [ ] Протестировать с несколькими последовательными действиями
- [ ] Добавить ограничение max_auto_continues (защита от зависаний)

### 4.2. Кастомный Vue.js фронтенд (опционально)
- [ ] Создать проект Vue 3 + TypeScript (Vite)
- [ ] Реализовать чат-интерфейс
- [ ] Список расследований
- [ ] Просмотр файлов расследования
- [ ] Создание нового расследования (форма)
- [ ] Интеграция с backend API



