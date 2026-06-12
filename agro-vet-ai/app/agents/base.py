from abc import ABC, abstractmethod

from langgraph.graph.state import CompiledStateGraph
from openai.types.chat import ChatCompletionMessage

from app.utils.logger import get_logger
from app.llm.providers.llm_provider import LLMProvider
from config.config import Config

cfg = Config.from_yaml()


class BaseAgent(ABC):
    def __init__(
            self,
            context: dict = None,
            dialog_history: list[dict[str, str]] = None
    ):
        super().__init__()
        self.llm_provider = LLMProvider()
        self.additional_context = context
        self.user_dialog_history = dialog_history

        self.llm_hyperparameters = None
        self.tools = None
        self.tools_by_name = None
        self.tools_open_ai = None

    def ask_llm(
            self,
            messages: list[dict],
            model: str = None,
            params: dict = None,
            tools: list[dict] = None,
            **kwargs
    ) -> ChatCompletionMessage:
        """
        Задать вопрос LLM через композицию.

        :param messages: Список сообщений с указанием роли.
        :param model: Модель для использования.
        :param params: Параметры llm модели.
        :param tools: Список инструментов.
        :return: Ответ от LLM.
        """
        return self.llm_provider.ask(
            messages=messages,
            model=model,
            params=params,
            tools=tools,
            **kwargs
        )

    @abstractmethod
    def build(self) -> CompiledStateGraph:
        """Создание графа действия агента."""
        raise NotImplementedError
