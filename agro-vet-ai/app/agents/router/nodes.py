import json

from langchain_core.messages import ToolMessage, ToolCall, AIMessage

from app.agents.base import BaseAgent
from app.agents.router.state import AgentState
from app.agents.router.prompts import ROUTER_AGENT_TOOLS_PROMPT, ROUTER_AGENT_FINAL_ANSWER_PROMPT
from config.config import Config
from app.utils.langchain_message_converters import to_openai_format

cfg = Config.from_yaml()


def tools_call_node(agent_instance: BaseAgent, state: AgentState) -> dict[str, list[ToolMessage]]:
    """
    Выполнение инструментов вызванных LLM.

    :param agent_instance: Instance of the agent
    :param state: Состояние агента.
    """
    agent_instance.logger.info(
        '[tools_call_node] Выполнение инструментов вызванных LLM')
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        # Если инструмент - это PCR или ELISA тест, добавляем file_path к аргументам, если он есть
        tool_args = tool_call["args"]
        if tool_call["name"] in ["process_with_pcr_test_interpretation", "process_with_elisa_test_interpretation"]:
            # Добавляем file_path только если он не None
            if state.get("file_path"):
                tool_args = {**tool_args,
                             "file_path": state.get("file_path")}
                agent_instance.logger.info(
                    f'Добавлен file_path к инструменту {tool_call["name"]}: {state.get("file_path")}')
            else:
                # Удаляем file_path из аргументов, если он там есть, чтобы не передавать None
                if "file_path" in tool_args:
                    del tool_args["file_path"]
                    agent_instance.logger.info(
                        f'Удален file_path из аргументов инструмента {tool_call["name"]}')

        if tool_call["name"] == "process_with_pharmacist":
            # Pass dialog history to pharmacist tool (excluding current user message to avoid duplication)
            # state["messages"][-1] is AIMessage with tool calls
            # state["messages"][-2] is the current HumanMessage (the question)
            history = [to_openai_format(msg) for msg in state["messages"][:-2]]
            tool_args["dialog_history"] = history
            if agent_instance.additional_context:
                tool_args["context"] = agent_instance.additional_context
            agent_instance.logger.info(f'Передача истории диалога ({len(history)} сообщений) инструменту {tool_call["name"]}')

        # Логируем вызов инструмента
        agent_instance.logger.info(
            f'Вызов инструмента: {tool_call["name"]} с аргументами: {tool_args}')

        try:
            text = agent_instance.tools_by_name[tool_call["name"]].invoke(tool_args)
        except Exception as e:
            # Обрабатываем ошибки вызова инструментов
            error_msg = f"Ошибка при вызове инструмента {tool_call['name']}: {str(e)}"
            agent_instance.logger.error(error_msg)
            text = (f"Извините, произошла ошибка при обработке запроса с помощью инструмента {tool_call['name']}. "
                    "Пожалуйста, попробуйте переформулировать вопрос.")

        # Parse JSON response to extract content and context
        try:
            tool_result = json.loads(text)
            content = tool_result.get("content", text)
            context = tool_result.get("context", "")
            context_images = tool_result.get("context_images", [])
            file_requests = tool_result.get("file_requests", [])
        except (json.JSONDecodeError, TypeError):
            # If not JSON, treat as plain text content
            content = text
            context = ""
            context_images = []
            file_requests = []

        outputs.append(
            ToolMessage(
                content=content,
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )

        if hasattr(agent_instance, 'expert_results'):
            agent_instance.expert_results.append({
                "tool": tool_call["name"],
                "context": context,
                "response": content,
                "context_images": context_images,
                "file_requests": file_requests,
            })
            agent_instance.logger.info(f'Добавлен ответ эксперта для инструмента {tool_call["name"]}')

    agent_instance.logger.info(
        f'Всего обработано инструментов: {len(state["messages"][-1].tool_calls)}')
    return {"messages": outputs}


def llm_call_node(agent_instance: BaseAgent, state: AgentState) -> dict[str, list]:
    """
    Генерация ответа агента.

    :param agent_instance: Instance of the agent
    :param state: Состояние агента.
    """
    agent_instance.logger.info('[llm_call_node] Генерация ответа агента')

    messages = [
        {"role": "system", "content": ROUTER_AGENT_TOOLS_PROMPT},
        *[json.loads(json.dumps(to_openai_format(msg))) for msg in state['messages']]
    ]

    response = agent_instance.ask_llm(
        messages=messages,
        params=agent_instance.llm_hyperparameters,
        tools=agent_instance.tools_open_ai,
    )

    if not response.tool_calls:
        return {"messages": [AIMessage(content=response.content)]}

    # Обрабатываем tool calls
    tool_calls = [
        ToolCall(
            name=t.function.name,
            args=json.loads(t.function.arguments),
            id=t.id
        )
        for t in response.tool_calls
    ]
    return {"messages": [AIMessage(content='', tool_calls=tool_calls)]}


def final_answer_node(agent_instance: BaseAgent, state: AgentState) -> dict[str, list]:
    """
       Генерация финального ответа агента.

       :param agent_instance: Instance of the agent
       :param state: Состояние агента.
    """
    agent_instance.logger.info('[final_answer_node] Генерация ответа агента')

    messages = [
        {"role": "system", "content": ROUTER_AGENT_FINAL_ANSWER_PROMPT},
        *[json.loads(json.dumps(to_openai_format(msg))) for msg in state['messages'][:-1]]
    ]

    response = agent_instance.ask_llm(
        messages=messages,
        params=agent_instance.llm_hyperparameters,
    )

    return {"messages": [AIMessage(content=response.content)]}
