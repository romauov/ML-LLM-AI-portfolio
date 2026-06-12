# Руководство по использованию promptfoo eval

Данное руководство описывает настройку и использование `promptfoo` для автоматической оценки качества ответов ветеринарного ИИ-ассистента.

## Требования

- **Node.js** версии 20 или выше
- **npm** (устанавливается вместе с Node.js)
- **Python** 3.8+ с активированным виртуальным окружением проекта
- **python-dotenv** (для загрузки переменных окружения из `.env` файла)

## Установка Node.js

### Windows

1. Скачайте LTS установщик Node.js с [nodejs.org](https://nodejs.org/)
2. Запустите установщик и следуйте инструкциям (используйте настройки по умолчанию)
3. Проверьте установку в командной строке:
   ```cmd
   node --version
   npm --version
   ```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y nodejs npm
```

Проверьте установку:
```bash
node --version
npm --version
```

## Установка promptfoo

После установки Node.js установите promptfoo глобально:

```bash
npm install -g promptfoo
```

Проверьте установку:
```bash
promptfoo --version
```

## Конфигурация тестов

### Переменные окружения

Все необходимые переменные окружения должны быть настроены в файле `.env` в корне проекта.

#### Для модели-судьи (LLM Judge):
- **`PROMPTFOO_API_URL`** — URL API для модели-судьи (например: `http://localhost:1234/v1` для LM Studio)
- **`PROMPTFOO_API_KEY`** — API ключ для модели-судьи (можно использовать любое значение для локальных моделей)
- **`PROMPTFOO_LOCAL_MODEL`** — название модели для оценки ответов (например: `qwen2.5:14b`)
- **`DEEPSEEK_API_KEY`** — API ключ для DeepSeek (если используется DeepSeek в качестве судьи)

Пример секции в `.env`:
```bash
# Promptfoo Judge (для оценки качества ответов)
PROMPTFOO_API_URL=http://localhost:1234/v1
PROMPTFOO_API_KEY=lm-studio
PROMPTFOO_LOCAL_MODEL=qwen2.5:14b

# Или для DeepSeek Judge
DEEPSEEK_API_KEY=your_deepseek_api_key
```

**Важно:** Команда `dotenv run` автоматически загружает переменные из `.env` файла перед запуском promptfoo.

## Запуск тестов

### Пошаговая инструкция

1. **Запустите API сервер проекта:**
   ```bash
   python main.py
   ```
   или
   ```bash
   docker compose up
   ```

2. **Откройте новый терминал и перейдите в корень проекта:**
   ```bash
   cd E:\projects\inline\agro-vet-ai
   ```

3. **Активируйте виртуальное окружение (если нужно):**

   **На Windows:**
   ```cmd
   .venv\Scripts\activate
   ```

   **На Linux:**
   ```bash
   source .venv/bin/activate
   ```

### Запуск тестов

**ВАЖНО: Запуск должен осуществляться из корня проекта с использованием `dotenv run` для загрузки переменных окружения:**

```bash
dotenv run promptfoo eval -c tests/promptfoo/test_avian_diagnosis.yaml
```

**Запуск с опциями:**
```bash
dotenv run promptfoo eval -c tests/promptfoo/test_avian_diagnosis.yaml --no-cache --verbose --output results/avian_test.json
```

**Другие тесты:**
```bash
dotenv run promptfoo eval -c tests/promptfoo/test_swine_diagnosis.yaml
dotenv run promptfoo eval -c tests/promptfoo/test_drugs_instructions.yaml
```

#### Объяснение параметров:

- **`-c tests\promptfoo\test_avian_diagnosis.yaml`** — путь к файлу конфигурации теста
- **`--no-cache`** — игнорирует кеш, всегда делает свежие запросы к API (полезно при отладке)
- **`--verbose`** — выводит подробные логи процесса выполнения тестов
- **`--output results/avian_test.json`** — указание пути для сохранения результатов в JSON файл для последующего анализа

### Просмотр результатов

**Веб-интерфейс (рекомендуется):**
```bash
promptfoo view -y
```

Флаг `-y` автоматически открывает браузер с интерфейсом результатов.