# DeepEval Tests

Тестирование качества RAG-ответов с использованием LLM-метрик через [DeepEval](https://github.com/confident-ai/deepeval).

## Запуск тестов

Запуск осуществляется из директории tests/deepeval

```bash
# Все тесты (автоматически находит все YAML в test_cases/)
python run_tests.py

# Конкретный файл
python run_tests.py -f test_cases/drugs_instructions.yaml

# Конкретный тест по ID
python run_tests.py -f test_cases/drugs_instructions.yaml -t drug_description_pulmosol

# С опциями pytest
python run_tests.py -v              # подробный вывод
python run_tests.py -x              # остановка на первой ошибке
python run_tests.py -f test_cases/file.yaml -t test_id -v -x  # комбинация
```

**Примечание**: Если указать несуществующий test_id, скрипт покажет список доступных тестов.

## Структура тест-кейса

Создайте YAML файл в `test_cases/`:

```yaml
# module - опционально (если не указан, используется имя файла)
module: "drugs_instructions"
description: "Тесты инструкций к препаратам"

test_cases:
  - id: test_1
    description: "Описание теста"
    query: "Вопрос к VetBot"
    expected_criteria:
      - "Критерий 1"
      - "Критерий 2"

metrics_config:
  geval_quality:
    provider: "deepseek"  # deepseek, vsegpt, openrouter, local
    model: "deepseek-chat"  # опционально (по умолчанию из config.yaml)
    threshold: 0.7
  answer_relevancy:
    provider: "deepseek"
    threshold: 0.7
  faithfulness:
    provider: "deepseek"
    threshold: 0.5
```

**Автоматическое определение module**: Если `module` не указан, используется имя файла (например, `drugs_instructions.yaml` → `drugs_instructions`).

Примеры: [test_cases/drugs_instructions.yaml](test_cases/drugs_instructions.yaml)

## Метрики

| Метрика | Описание | Порог |
|---------|----------|-------|
| **GEval** | Оценка качества по критериям (недетерминистичная, variance ~0.1) | 0.7 |
| **AnswerRelevancyMetric** | Релевантность ответа запросу | 0.7 |
| **FaithfulnessMetric** | Соответствие контексту (только если VetBot вернул retrieval_context) | 0.5 |

**Важно**:
- GEval недетерминистичная - для критичных тестов запускайте несколько раз
- FaithfulnessMetric применяется только если API вернул `context`

## Провайдеры LLM для оценки

Настройка в `.env`:

```bash
# DeepSeek (рекомендуется: быстро, дёшево)
DEEPSEEK_API_KEY="sk-..."

# VseGPT
VSEGPT_API_KEY="sk-..."
VSEGPT_BASE_URL="https://api.vsegpt.ru/v1"

# OpenRouter
OPENROUTER_API_KEY="sk-..."
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"

# Local (из config.yaml)
INLINE_API_KEY="..."
INLINE_BASE_URL="INLINE_URL"
```

Использование в YAML:

```yaml
metrics_config:
  geval_quality:
    provider: "deepseek"  # или vsegpt, openrouter, local
    model: "deepseek-chat"  # опционально
    threshold: 0.7
```

Если `model` не указан, используется значение по умолчанию из `config.yaml` для выбранного провайдера.

## Просмотр результатов

```bash
python run_viewer.py              # откроет браузер на http://localhost:8000
python run_viewer.py -p 9000      # другой порт
python run_viewer.py -d /path/to/results  # другая директория
```

URL веб-интерфейса: `http://localhost:8000/utils/viewer_templates/viewer.html`

Результаты сохраняются в:
- `results/test_results_{timestamp}.json`
- `logs/YYYY-MM-DD/app.log`