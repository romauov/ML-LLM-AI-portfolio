# Telegram Bot Manager API

Проект предоставляет API для управления Telegram ботами на основе FastAPI. Ключевая особенность системы - автоматическая генерация уникальных роутеров и промтов для каждого бота на основе его конфигурации.

## Основные возможности

- **Динамический запуск ботов**: Запуск новых ботов через API без перезагрузки сервера
- **Автоматическая генерация роутеров**: Каждый бот получает уникальную логику обработки сообщений
- **Интеллектуальные промты**: Автоматическое создание промтов на основе данных из Google Sheets
- **Управление конфигурацией**: Гибкая настройка каждого бота через API
- **Мультибот поддержка**: Одновременная работа множества независимых ботов
- **Асинхронная архитектура**: Высокая производительность на основе FastAPI и aiogram

## Автоматическая генерация роутеров

Система автоматически создает уникальный роутер для каждого бота при его запуске. Роутер содержит всю логику обработки сообщений для конкретного бота.

### Ключевые компоненты роутера:

```python
def generate_router(client_name, table_id, sheet_id, channel_id, manager_ids) -> Router:
    router = Router()
    conversator = Conversator(client_name, table_id, sheet_id)

    # Обработка команды /start
    @router.message(CommandStart())
    async def send_welcome(message: Message):
        # Логика приветствия

    # Обновление инструкций
    @router.message(Command('update'))
    async def update_instructions(message: Message):
        # Обновление промтов

    # Основной обработчик сообщений
    @router.message()
    async def generate_reply_message(message: Message, bot: Bot):
        # Логика обработки сообщений
        # Пересылка сообщений в канал
        # Генерация ответов
        # Уведомление менеджеров
        # Обработка ошибок
```

### Особенности генерации роутеров:
- **Интеграция с Conversator**: Каждый роутер использует экземпляр Conversator для генерации ответов
- **Пересылка сообщений**: Все сообщения автоматически пересылаются в указанный канал
- **Обработка ошибок**: Автоматическое уведомление об ошибках в специальный канал
- **Интерактивные кнопки**: Динамическое создание клавиатуры на основе конфигурации

## Автоматическая генерация промтов

Система автоматически генерирует промты для ботов на основе данных из Google Sheets:

```python
def load_files(table_id, sheet_id, price_id=None, price_sheet=None):
    promt_table = load_from_google_sheet(table_id, sheet_id)
    promt_table = promt_table.iloc[:, 0:2]
    first_col = promt_table.iloc[:, 0]

    conversator_data = {}
    conversator_data['buttons'] = get_buttons(promt_table, first_col)
    conversator_data['reglament'] = create_promt(promt_table, first_col)
    conversator_data['tools'] = extract_tools(first_col)
    if price_id is not None and price_sheet is not None:
        conversator_data['price_list'] = load_from_google_sheet(
            price_id, price_sheet)
    return conversator_data
```

### Процесс генерации промтов:
1. **Загрузка данных**: Получение данных из Google Sheets по указанному ID таблицы и листа
2. **Обработка данных**: Фильтрация и преобразование данных в подходящий формат
3. **Генерация промта**: Использование ИИ-модели (Gemini 2.5) для создания оптимизированного промта
4. **Извлечение кнопок**: Автоматическое создание интерактивных кнопок на основе данных

## Технологический стек

- **Python 3.10+**: Основной язык программирования
- **FastAPI**: Веб-фреймворк для создания API
- **aiogram 3.x**: Библиотека для работы с Telegram ботами
- **Pydantic**: Валидация данных и работа с моделями
- **Pandas**: Обработка табличных данных
- **OpenAI API**: Генерация промтов с помощью ИИ

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone {{GITLAB_URL}}/romauov/axe-tg-bots.git
cd axe-tg-bots
```

2. Настройте переменные окружения (создайте файл `.env`):
```bash
touch .env
nano .env
```
```env
openai_key=<<VSEGPT-API-KEY>>
openai_proxy=https://api.vsegpt.ru/v1
```
3. [Создайте json-ключ для доступа к Google API](google_api_instructions.md) и разместите его в корне проекта с именем `google_credentials.json`

4. Запустите сервер:
```bash
docker compose up -d
```


## Использование API

### Запуск нового бота
```bash
curl -X POST "http://localhost:8181/clients/" \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "meatinfo_bot",
    "table_id": "1aBcD3fG5h",
    "sheet_id": "Sheet1",
    "price_id": "1aBcD3fG5h",
    "price_sheet": "Sheet1",
    "channel_id": "@meatinfo_test",
    "manager_ids": [123456789],
    "token": "1234567890:ABCdefGHIjklMNopQRSTuvwXYZ123456"
  }'
```

### Получение списка активных ботов
```bash
curl "http://localhost:8181/clients/"
```

### Остановка и удаление бота
```bash
curl -X DELETE "http://localhost:8181/clients/{bot_name}"
```

### Остановка всех ботов
```bash
curl -X POST "http://localhost:8181/shutdown" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Архитектура системы

```
├── app/
│   ├── bot_manager.py       # Менеджер ботов (запуск/остановка)
│   ├── router.py            # Роутер FastAPI
│   └── schemas.py           # Pydantic модели данных
├── conversator/
│   ├── conversator.py       # Класс для генерации ответов
│   ├── chat_history.py      # Управление историей сообщений
│   ├── router_generator.py  # генератор роутера aiogram
│   ├── chat_history.py      # Управление историей сообщений
│   ├── file_loader.py       # Загрузчик данных для генерации промтов
│   └── tools.py             # инструменты модели генерации
├── utils/
│   ├── aiogram_keyboards.py # Генератор интерактивных клавиатур
│   ├── client.py            # Клиент для работы с OpenAI API
│   ├── errors.py            # Обработка ошибок
│   ├── logger.py            # Настройка логгирования
│   ├── remove_md.py         # Утилиты для работы с Markdown
│   └── setting.py           # секреты проекта
├── Dokerfile
├── docker-compose.yaml
├── requirements.txt
└── README.md
```

## Особенности реализации

1. **Динамическая генерация роутеров**:
   - Каждый бот получает уникальную логику обработки сообщений
   - Автоматическая интеграция с Conversator для генерации ответов
   - Гибкая система обработки команд и сообщений

2. **Интеллектуальные промты**:
   - Автоматическое создание промтов на основе данных из Google Sheets
   - Использование ИИ для оптимизации промтов
   - Динамическое обновление промтов без перезапуска бота

3. **Управление историей диалогов**:
   - Сохранение истории сообщений для каждого пользователя
   - Суммаризация диалогов для менеджеров
   - Контекстное взаимодействие с пользователями

4. **Расширяемая архитектура**:
   - Поддержка различных ИИ-моделей
   - Гибкая система инструментов (tools) для расширения функционала
   - Возможность интеграции с различными источниками данных


## Авторы

- Sergei Romanov - [romauov]({{GITLAB_URL}}/romauov)