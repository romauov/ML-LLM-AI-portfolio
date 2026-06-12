from abc import ABC, abstractmethod
from typing import Dict
from app.llm.providers.llm_provider import LLMProvider
from openai.types.chat import ChatCompletionMessage
from app.utils.logger import get_logger


class BaseTopic(ABC):
    """
    Абстрактный класс обработки вопросов.
    """

    def __init__(self):
        self.llm_provider = LLMProvider()

    @abstractmethod
    def process(
            self,
            question: str,
            context: dict = None,
            dialog_history: list[dict[str, str]] = None,
            file_path: str = None
    ) -> Dict[str, str | None]:
        """
        Обработать вопрос.

        :param question: Вопрос пользователя
        :param context: Дополнительный контекст (опционально)
        :param dialog_history: История диалога пользователя
        :param file_path: Путь к файлу
        :return: Словарь с тэгом и контентом ответа
        """
        raise NotImplementedError

    def ask_llm(
            self,
            messages: list[dict],
            model: str = None,
            params: dict = None,
            *args, **kwargs
    ) -> ChatCompletionMessage:
        """
        Задать вопрос LLM через композицию.

        :param messages: Список сообщений с указанием роли.
        :param model: Модель для использования.
        :param params: Параметры llm модели.
        :return: Ответ от LLM.
        """
        return self.llm_provider.ask(
            messages=messages,
            model=model,
            params=params,
            *args, **kwargs
        )

    @staticmethod
    def prompts_to_messages(
            system: str,
            user: str,
            dialog_history: list[dict] = None
    ) -> list[dict]:
        messages = [{"role": "system", "content": system}]
        if dialog_history:
            messages.extend(dialog_history)
        messages.append({"role": "user", "content": user})
        return messages
