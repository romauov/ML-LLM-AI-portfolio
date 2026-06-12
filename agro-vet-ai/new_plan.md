Отлично, теперь картина полная. Вот детальный план:

---

## Детальный план изменений `router_v2`

### Архитектурная идея

```
Пользователь
     ↓
AgentExecutor (LLM #1 — выбор инструмента)
     ↓
on_tool_end → определяем группу инструмента → меняем системный промпт
     ↓
AgentExecutor (LLM #2 — финальный ответ с новым промптом)
     ↓
Стриминг ответа пользователю
```

Для диагностических инструментов (`swine`, `avian`, `pcr`, `elisa`) — инструменты перестают вызывать свой LLM, возвращают только данные. Финальный LLM агента формирует ответ на основе этих данных + специфического промпта.

---

### Изменение 1 — `tools.py`: инструменты диагностики возвращают данные, а не готовый ответ

Сейчас `process_with_swine_disease_diagnosis` и `process_with_avian_disease_diagnosis` вызывают `handler.process()`, который внутри делает `ask_llm()` и возвращает уже готовый текст. Агент получает готовый ответ и тратит ещё один LLM-вызов на его «пересказ».

**Решение:** Вынести логику поиска релевантных данных из `topic_handler.process()` в отдельный метод, вызывать только его из инструмента.

```python
# tools.py — новая версия

@tool(parse_docstring=True)
def process_with_avian_disease_diagnosis(question: str) -> str:
    """
    Поиск релевантной информации о болезнях птиц по симптомам.
    Возвращает структурированные данные из базы знаний для диагностики.

    Args:
        question: Вопрос о болезнях птиц, симптомах, диагностике.
    """
    handler = AvianDiseasesDiagnosis()
    # Вызываем только поиск, без LLM
    relevant_content = handler.relevant_content(question)
    context_text = "\n\n".join(relevant_content) if relevant_content else ""
    
    if not context_text:
        return "Релевантная информация о болезнях птиц не найдена."
    
    return context_text


@tool(parse_docstring=True)
def process_with_swine_disease_diagnosis(question: str) -> str:
    """
    Поиск релевантной информации о болезнях свиней по симптомам.
    Возвращает структурированные данные из базы знаний для диагностики.

    Args:
        question: Вопрос о болезнях свиней, симптомах, диагностике.
    """
    handler = SwineDiseasesDiagnosis()
    relevant_content = handler.relevant_content(question)
    context_text = "\n\n".join(relevant_content) if relevant_content else ""
    
    if not context_text:
        return "Релевантная информация о болезнях свиней не найдена."
    
    return context_text
```

**Для PCR и ELISA** — хендлеры сложнее (работают с PDF через `BaseImageTopic`). Если файла нет, возвращают ошибку — это ожидаемо. Если файл есть — делают 2 LLM-вызова внутри (`extraction_prompt` + `analysis_prompt`). Здесь выносить нечего: данные — это уже интерпретированный PDF. Оставляем как есть, но меняем то, что агент делает с результатом (через промпт — см. Изменение 3).

---

### Изменение 2 — `agent.py`: отслеживание вызванного инструмента и перехват для динамического промпта

Ключевая механика: в `astream_events` при `on_tool_end` сохраняем группу инструмента. Затем в `on_chat_model_stream` (финальный LLM-ответ) уже стримим с учётом того, какой инструмент был последним. Для этого агент пересоздаётся **до первого запуска** с пустым `tool_instructions`, а если нужен второй проход — этот механизм уже не нужен, потому что мы меняем промпт **перед** финальным LLM-вызовом.

Реальная проблема: `AgentExecutor` — это цикл, и нельзя изменить промпт посередине. Нужно использовать другой механизм.

**Решение через `RunnableConfig` + кастомный `BaseChatModel` wrapper:**

Нет. Это сложно. Более простой и надёжный способ:

**Решение через два отдельных вызова:**

```
1. AgentExecutor с tool_instructions="" → агент выбирает инструмент и получает данные
2. После on_tool_end — запускаем отдельный стриминг-вызов LLM с нужным промптом
```

Но тогда второй вызов не через `AgentExecutor`, а напрямую через `ChatOpenAI`. Это позволяет полностью контролировать промпт и стримить ответ.

**Итоговая архитектура `process_stream`:**

```python
async def process_stream(self, question, file_path=None, user_id=None):
    # ШАГ 1: Агент выбирает инструмент и выполняет его
    tool_results = await self._run_tool_selection(question)
    # tool_results = {"tool_name": str, "tool_output": str, "tool_group": str}
    
    # ШАГ 2: Стриминг финального ответа с динамическим промптом
    async for chunk in self._stream_final_answer(question, tool_results):
        yield chunk
```

```python
async def _run_tool_selection(self, question: str) -> dict:
    """
    Запускает AgentExecutor БЕЗ стриминга до момента on_tool_end.
    Возвращает имя инструмента, его вывод и группу.
    Если агент решает ответить без инструмента — возвращает None.
    """
    agent_executor = self._get_agent_executor()
    agent_input = self._build_agent_input(question)
    
    tool_name = None
    tool_output = None
    
    async for event in agent_executor.astream_events(agent_input, version="v2"):
        kind = event["event"]
        
        if kind == "on_tool_start":
            tool_name = event["name"]
            # yield уведомление пользователю о начале работы инструмента
            # (через отдельный yield-очередь или callback — см. ниже)
            
        elif kind == "on_tool_end":
            tool_output = event["data"].get("output", "")
            break  # Прерываем после первого инструмента
    
    if tool_name is None:
        return {"tool_name": None, "tool_output": None, "tool_group": None}
    
    tool_group = TOOL_GROUP_MAP.get(tool_name)
    return {
        "tool_name": tool_name,
        "tool_output": tool_output,
        "tool_group": tool_group,
    }
```

**Проблема с `break` в `astream_events`:** прерывание генератора может вызвать ошибки в LangChain. Нужно использовать флаг:

```python
found_tool_result = False
async for event in agent_executor.astream_events(agent_input, version="v2"):
    if found_tool_result:
        continue  # дренируем генератор
    ...
    elif kind == "on_tool_end":
        tool_output = ...
        found_tool_result = True
```

Или, что лучше — использовать `agent_executor.ainvoke()` с `return_intermediate_steps=True`. Тогда всё выполнение (выбор инструмента + вызов) происходит синхронно, и мы получаем `intermediate_steps` с результатами:

```python
result = await agent_executor.ainvoke(agent_input)
steps = result.get("intermediate_steps", [])
# steps = [(AgentAction(tool=..., tool_input=...), tool_output), ...]
last_action, last_output = steps[-1] if steps else (None, None)
tool_name = last_action.tool if last_action else None
tool_group = TOOL_GROUP_MAP.get(tool_name) if tool_name else None
```

Это надёжнее и без проблем с дренированием генератора. Плюс — `intermediate_steps` уже есть в `AgentExecutor` (параметр `return_intermediate_steps=True` уже установлен).

---

### Изменение 3 — `prompts.py`: разбивка промпта и инструкции по группам

```python
# prompts.py

ROUTER_BASE_PROMPT = """
Вы являетесь экспертом по ветеринарной медицине.
Ваша задача - ответить на вопрос пользователя, используя доступные инструменты для поиска информации.

## Доступные инструменты
... (вся секция инструментов без изменений) ...

## ПРИНЦИПЫ ВЗАИМОДЕЙСТВИЯ
... (без изменений) ...

## РАБОЧИЙ ПРОЦЕСС
... (без изменений) ...

## Обработка follow-up вопросов
... (без изменений) ...
"""

# Секция динамически добавляется после вызова инструмента
TOOL_FOLLOWUP_INSTRUCTIONS = {
    "librarian": """
## ИНСТРУКЦИЯ ПО ФОРМИРОВАНИЮ ОТВЕТА (активна после поиска по книгам)

Ты получил контекст из научной/учебной литературы. Сформируй структурированный ветеринарный ответ:

1. Дай прямой ответ на вопрос, опираясь только на полученные данные
2. Структурируй по разделам если данных много (этиология, симптомы, лечение и т.д.)
3. В конце добавь блок **Источники:** с перечнем книг из контекста
4. Если в тексте упоминаются конкретные препараты (торговые названия или МНН) —
   добавь в конце: "💊 Уточнить информацию о препаратах можно через фармацевта."
""",

    "pharmacist": """
## ИНСТРУКЦИЯ ПО ФОРМИРОВАНИЮ ОТВЕТА (активна после поиска препаратов)

Ты получил данные из базы препаратов. Сформируй ответ:

1. Если найден один препарат — структурируй по разделам инструкции
2. Если найдено несколько — дай сравнительный обзор, выдели ключевые различия
3. Если получен список для уточнения — передай его пользователю без изменений
4. Всегда напоминай: применение препаратов только под наблюдением ветеринара
5. Не добавляй информацию, которой нет в полученных данных
""",

    "diagnosis_avian": """
## ИНСТРУКЦИЯ ПО ФОРМИРОВАНИЮ ОТВЕТА (активна для диагностики птиц)

Ты получил структурированные данные о болезнях птиц из базы знаний.
Сформируй дифференциальный диагноз:

1. Перечисли наиболее вероятные заболевания с кратким обоснованием по симптомам
2. Опиши ключевые отличительные признаки для дифференциации
3. Укажи рекомендуемые диагностические мероприятия
4. Обязательно: рекомендуй немедленную изоляцию при подозрении на особо опасные болезни
   (Ньюкасл, грипп птиц, инфекционный бронхит)
""",

    "diagnosis_swine": """
## ИНСТРУКЦИЯ ПО ФОРМИРОВАНИЮ ОТВЕТА (активна для диагностики свиней)

Ты получил структурированные данные о болезнях свиней из базы знаний.
Сформируй дифференциальный диагноз:

1. Перечисли наиболее вероятные заболевания с кратким обоснованием по симптомам
2. Опиши ключевые отличительные признаки для дифференциации
3. Укажи рекомендуемые диагностические мероприятия
4. Обязательно: при симптомах АЧС — немедленно уведомить ветеринарные службы,
   ввести карантин
""",

    "lab_test": """
## ИНСТРУКЦИЯ ПО ФОРМИРОВАНИЮ ОТВЕТА (активна для лабораторных тестов)

Ты получил уже интерпретированный результат лабораторного теста от специализированного модуля.
Передай его пользователю В ТОЧНОСТИ КАК ЕСТЬ, без изменений, добавлений и сокращений.
Не добавляй вступлений типа "На основании результатов..." или "Согласно данным...".
""",
}

TOOL_GROUP_MAP = {
    "search_database_by_all_books": "librarian",
    "search_database_by_one_book": "librarian",
    "get_page_content": "librarian",
    "get_list_of_books": "librarian",
    "get_books_content": "librarian",
    "search_by_trade_name": "pharmacist",
    "search_by_active_substance": "pharmacist",
    "search_by_conditions": "pharmacist",
    "get_drug_full_info": "pharmacist",
    "process_with_avian_disease_diagnosis": "diagnosis_avian",
    "process_with_swine_disease_diagnosis": "diagnosis_swine",
    "process_with_pcr_test_interpretation": "lab_test",
    "process_with_elisa_test_interpretation": "lab_test",
}
```

---

### Изменение 4 — `agent.py`: финальный стриминг с динамическим промптом

```python
def _build_dynamic_prompt(self, tool_group: str | None) -> ChatPromptTemplate:
    """Собирает промпт с учётом вызванного инструмента."""
    followup = TOOL_FOLLOWUP_INSTRUCTIONS.get(tool_group, "") if tool_group else ""
    system = ROUTER_BASE_PROMPT
    if followup:
        system = system + "\n\n" + followup
    
    return ChatPromptTemplate.from_messages([
        ("system", system),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
```

```python
async def process_stream(self, question, file_path=None, user_id=None):
    try:
        hint = build_abbreviation_hint(question)
        enriched = f"{hint}\n\n{question}" if hint else question
        agent_input = self._build_agent_input(enriched)

        # ШАГ 1: ainvoke — выбор и выполнение инструмента (без стриминга)
        # Уведомляем пользователя что идёт обработка
        yield {"node": "tool_start", "data": {"tool": "thinking", "input": {}}}
        
        executor_static = self._get_agent_executor()  # с базовым промптом
        result = await executor_static.ainvoke(agent_input)
        
        steps = result.get("intermediate_steps", [])
        tool_group = None
        tool_name = None
        
        if steps:
            last_action, last_output = steps[-1]
            tool_name = last_action.tool
            tool_group = TOOL_GROUP_MAP.get(tool_name)
            
            # Уведомляем об окончании инструмента
            yield {
                "node": "tool_end",
                "data": {"tool": tool_name, "summary": self._tool_summary(tool_name, last_output)},
            }

        # ШАГ 2: Стриминг финального ответа с динамическим промптом
        dynamic_prompt = self._build_dynamic_prompt(tool_group)
        llm = self._get_llm()
        agent_dynamic = create_openai_tools_agent(llm, self.tools, dynamic_prompt)
        
        # Для финального шага передаём agent_scratchpad с уже выполненными шагами
        # чтобы LLM видел результаты инструмента
        chain = dynamic_prompt | llm
        
        # Строим messages вручную: system + chat_history + human + tool_result
        messages = self._build_messages_with_tool_result(
            question=enriched,
            tool_name=tool_name,
            tool_output=last_output if steps else None,
        )
        
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield {"node": "llm_stream", "data": {"content": chunk.content}}

    except Exception as e:
        self.logger.error(f"Error in process_stream: {e}")
        yield {"error": str(e)}
```

```python
def _build_messages_with_tool_result(
    self, question: str, tool_name: str | None, tool_output: str | None,
    tool_group: str | None = None
) -> list:
    """
    Формирует список сообщений для финального LLM-вызова:
    system (с динамическим промптом) + chat_history + human + tool_result (как assistant message).
    """
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
    
    followup = TOOL_FOLLOWUP_INSTRUCTIONS.get(tool_group, "") if tool_group else ""
    system_text = ROUTER_BASE_PROMPT + ("\n\n" + followup if followup else "")
    
    messages = [SystemMessage(content=system_text)]
    
    # История диалога
    if self.user_dialog_history:
        for msg in self.user_dialog_history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))
    
    messages.append(HumanMessage(content=question))
    
    # Результат инструмента добавляем как контекст
    if tool_name and tool_output:
        tool_result_text = f"[Результат инструмента {tool_name}]:\n{tool_output}"
        messages.append(AIMessage(content=tool_result_text))
    
    return messages
```

---

### Изменение 5 — `librarian_tools.py` + `pharmacist_utils.py`: вызов `extract_substances_and_build_footnote`

Функция `extract_substances_and_build_footnote` извлекает МНН из ответа библиотекаря через LLM и дополняет его ссылками на препараты из каталога. Сейчас она нигде не вызывается в `router_v2`.

Логичное место вызова — **после** того как агент сформировал финальный ответ по librarian-данным. Но это уже пост-обработка стрима, и вставить её в середину потока нельзя.

**Решение:** Вызывать её в `process_stream` **после завершения стриминга** как отдельный блок:

```python
# В process_stream, после цикла стриминга финального ответа:

if tool_group == "librarian":
    # Собираем весь стримленный текст
    full_response = "".join(accumulated_chunks)
    
    footnote = extract_substances_and_build_footnote(
        response_text=full_response,
        agent_instance=self,
    )
    if footnote:
        yield {"node": "llm_stream", "data": {"content": footnote}}
```

Для этого нужно накапливать чанки в `accumulated_chunks = []` и после цикла делать вызов. Это добавляет ещё один LLM-вызов, но он явный и контролируемый — только для librarian-группы.

---

### Итоговый список файлов к изменению

| Файл | Что меняем |
|---|---|
| `tools.py` | `process_with_swine/avian_diagnosis` — убираем `handler.process()`, используем только `handler.relevant_content()` |
| `prompts.py` | Разбить на `ROUTER_BASE_PROMPT` + `TOOL_FOLLOWUP_INSTRUCTIONS` + `TOOL_GROUP_MAP` |
| `agent.py` | `process_stream` — два шага: `ainvoke` для инструмента + `astream` для финального ответа с динамическим промптом; `_build_dynamic_prompt`, `_build_messages_with_tool_result` |
| `pharmacist_utils.py` | `extract_substances_and_build_footnote` — добавить вызов из `process_stream` для librarian-группы |

---