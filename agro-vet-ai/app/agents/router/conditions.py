from app.agents.base import BaseAgent
from app.agents.router.state import AgentState
from config.config import Config

cfg = Config.from_yaml()


def llm_call_condition(agent_instance: BaseAgent, state: AgentState) -> str:
    """
    Проверка последнего сообщения в состоянии агента и последующий выбор ноды к которой надо перейти.

    :param agent_instance: Instance of the agent
    :param state: Состояние агента.
    """
    agent_instance.logger.info(
        '[llm_call_condition] Проверка последнего сообщения в состоянии агента')

    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, 'tool_calls', None)
    if tool_calls:
        if hasattr(agent_instance, 'attempts'):
            agent_instance.attempts += 1
            if agent_instance.attempts > cfg.router_agent.max_attempts:
                return "end_by_limit"
        return "continue"
    return "end"


def tools_call_condition(agent_instance: BaseAgent, state: AgentState) -> str:
    """
    Определение следующего узла на основе результатов валидации.

    :param agent_instance: Instance of the agent
    :param state: Состояние агента.
    :return: Имя следующего узла
    """
    agent_instance.logger.info(
        '[validation_condition] Определение следующего узла на основе результатов валидации')

    return "continue"
