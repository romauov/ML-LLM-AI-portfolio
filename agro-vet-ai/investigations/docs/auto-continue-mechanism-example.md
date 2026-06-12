# Механизм автоматического продолжения работы агента

## Описание подхода

Механизм определения, должен ли агент продолжать работу или передать управление пользователю, реализуется через дополнительный инструмент `respond_in_schema` и специальное системное сообщение.

## Источник

**Оригинальная реализация:** [QwenLM/qwen-code](https://github.com/QwenLM/qwen-code)

⚠️ **ВАЖНО:** Перед реализацией этого механизма необходимо:
1. Изучить исходный код Qwen Code в репозитории
2. Понять детали реализации агентного цикла
3. Проанализировать edge cases и обработку ошибок
4. Адаптировать подход для нашего ветеринарного агента

Данный документ содержит концептуальное описание механизма, но финальная реализация должна основываться на детальном изучении оригинального кода.

## Реализация

### 1. Добавление инструмента `respond_in_schema`

К списку доступных агенту инструментов добавляется специальный tool:

```json
{
  "name": "respond_in_schema",
  "description": "Provide the response in provided schema",
  "parameters": {
    "type": "object",
    "properties": {
      "reasoning": {
        "type": "string",
        "description": "Brief explanation justifying the 'next_speaker' choice based *strictly* on the applicable rule and the content/structure of the preceding turn."
      },
      "next_speaker": {
        "type": "string",
        "enum": [
          "user",
          "model"
        ],
        "description": "Who should speak next based *only* on the preceding turn and the decision rules"
      }
    },
    "required": [
      "reasoning",
      "next_speaker"
    ]
  }
}
```

### 2. Инъекция проверочного сообщения

После получения ответа от модели, к цепочке сообщений добавляется специальное User-сообщение:

```
Analyze *only* the content and structure of your immediately preceding response (your last turn in the conversation history). Based *strictly* on that response, determine who should logically speak next: the 'user' or the 'model' (you).

**Decision Rules (apply in order):**
1.  **Model Continues:** If your last response explicitly states an immediate next action *you* intend to take (e.g., "Next, I will...", "Now I'll process...", "Moving on to analyze...", indicates an intended tool call that didn't execute), OR if the response seems clearly incomplete (cut off mid-thought without a natural conclusion), then the **'model'** should speak next.
2.  **Question to User:** If your last response ends with a direct question specifically addressed *to the user*, then the **'user'** should speak next.
3.  **Waiting for User:** If your last response completed a thought, statement, or task *and* does not meet the criteria for Rule 1 (Model Continues) or Rule 2 (Question to User), it implies a pause expecting user input or reaction. In this case, the **'user'** should speak next.
```

### 3. Обработка ответа

Модель вызывает `respond_in_schema` с параметрами:
- `reasoning`: краткое объяснение решения
- `next_speaker`: `"user"` или `"model"`

Backend анализирует ответ:
- Если `next_speaker == "model"` → убрать проверочное сообщение из истории, продолжить агентный цикл
- Если `next_speaker == "user"` → убрать проверочное сообщение, вернуть ответ пользователю

## Преимущества подхода

1. **Не требует изменения основного системного промпта** - вся логика инкапсулирована в отдельном инструменте
2. **Явная структура решения** - модель должна обосновать свой выбор
3. **Четкие правила** - три простых правила в порядке приоритета
4. **Самоанализ** - модель анализирует свой собственный последний ответ

## Пример работы

### Сценарий 1: Агент должен продолжить

**Последний ответ агента:**
```
Я обнаружил информацию о E.coli в базе знаний. Теперь я прочитаю файл hypotheses.md, чтобы обновить гипотезы.
```

**Вызов respond_in_schema:**
```json
{
  "reasoning": "The response explicitly states the next action: 'Now I will read hypotheses.md to update hypotheses', indicating the model intends to continue working.",
  "next_speaker": "model"
}
```

**Результат:** Backend продолжает агентный цикл, агент выполняет `read_file`.

---

### Сценарий 2: Передача пользователю (вопрос)

**Последний ответ агента:**
```
Я обновил файл hypotheses.md с тремя основными гипотезами. Основная гипотеза - E.coli инфекция.

Для уточнения диагноза мне нужна дополнительная информация: проводились ли лабораторные исследования фекалий поросят?
```

**Вызов respond_in_schema:**
```json
{
  "reasoning": "The response ends with a direct question to the user about laboratory tests, meeting Rule 2.",
  "next_speaker": "user"
}
```

**Результат:** Backend возвращает ответ пользователю и ожидает ввода.

---

### Сценарий 3: Передача пользователю (завершение)

**Последний ответ агента:**
```
Я завершил первичный анализ и создал файл report.md с предварительными выводами. Основные файлы расследования обновлены.
```

**Вызов respond_in_schema:**
```json
{
  "reasoning": "The response indicates completion of a task ('finished preliminary analysis', 'updated investigation files') without stating further immediate actions or asking questions. Rule 3 applies - waiting for user input.",
  "next_speaker": "user"
}
```

**Результат:** Backend возвращает ответ пользователю.

## Адаптация для ветеринарного агента

Правила остаются теми же, но примеры в промпте могут быть адаптированы:

**Rule 1 примеры для ветеринарного контекста:**
- "Теперь я поищу информацию о диарее поросят..."
- "Далее обновлю файл hypotheses.md..."
- "Мне нужно прочитать карточку группы для уточнения возраста..."

**Rule 2 примеры:**
- "Проводилась ли вакцинация против [патоген]?"
- "Какая кормовая программа использовалась для этой группы?"
- "Когда именно начались первые симптомы?"

## Технические детали реализации

### Backend (FastAPI)

```python
async def agent_turn_loop(messages: List[dict], investigation_id: str):
    """
    Основной агентный цикл с механизмом auto-continue
    """
    while True:
        # 1. Получить ответ от LLM
        response = await llm_service.chat_completion(
            messages=messages,
            tools=get_all_tools_including_respond_in_schema()
        )

        # 2. Обработать tool calls (если есть)
        if response.tool_calls:
            # Выполнить MCP инструменты
            tool_results = await execute_tool_calls(response.tool_calls)
            messages.append(response)
            messages.extend(tool_results)
        else:
            # Нет tool calls - добавить текстовый ответ
            messages.append(response)

        # 3. Проверка необходимости продолжения
        should_continue = await check_if_should_continue(messages)

        if not should_continue:
            # Вернуть результат пользователю
            return extract_user_facing_response(messages)

        # Иначе продолжить цикл


async def check_if_should_continue(messages: List[dict]) -> bool:
    """
    Добавить проверочное сообщение и получить решение от модели
    """
    # Создать копию для проверки
    check_messages = messages.copy()

    # Добавить проверочное сообщение
    check_messages.append({
        "role": "user",
        "content": CONTINUE_CHECK_PROMPT
    })

    # Получить ответ с respond_in_schema
    response = await llm_service.chat_completion(
        messages=check_messages,
        tools=[respond_in_schema_tool],
        tool_choice={"type": "function", "function": {"name": "respond_in_schema"}}
    )

    # Извлечь решение
    tool_call = response.tool_calls[0]
    decision = json.loads(tool_call.function.arguments)

    logger.info(f"Continue decision: {decision['next_speaker']} - {decision['reasoning']}")

    return decision["next_speaker"] == "model"
```

### Важные моменты

1. **Проверочное сообщение не сохраняется** в истории диалога - оно используется только для принятия решения
2. **tool_choice принудительный** - модель должна вызвать именно `respond_in_schema`
3. **Логирование решений** - важно отслеживать, почему агент решил продолжить или остановиться
4. **Ограничение циклов** - добавить max_iterations для предотвращения бесконечных циклов

## Альтернативный подход: эвристики

Можно комбинировать с эвристиками на стороне backend:

```python
def heuristic_should_continue(last_message: dict) -> Optional[bool]:
    """
    Быстрые эвристики перед вызовом respond_in_schema
    """
    content = last_message.get("content", "")

    # Если есть невыполненные tool_calls - продолжить
    if last_message.get("tool_calls"):
        return True

    # Если заканчивается явным вопросом на русском - остановиться
    if content.strip().endswith("?"):
        return False

    # Если есть фразы-индикаторы продолжения
    continue_indicators = [
        "далее я", "теперь я", "следующий шаг",
        "сейчас обновлю", "теперь прочитаю"
    ]
    if any(ind in content.lower() for ind in continue_indicators):
        return True

    # Неопределенно - использовать respond_in_schema
    return None
```

Это может сэкономить вызовы к LLM в очевидных случаях.
