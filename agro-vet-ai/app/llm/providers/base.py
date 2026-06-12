from abc import ABC, abstractmethod
from typing import Optional, NamedTuple

from openai import OpenAIError, OpenAI
from openai.types.chat import ChatCompletionMessage

from config.config import Config
from app.llm.providers.utils import clean_model_response
from app.utils.logger import get_logger
from app.utils.settings import secrets as s


class EmbeddingResult(NamedTuple):
    vector: list[float]
    column: str


class BaseLLMProvider(ABC):
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

        cfg = Config.from_yaml()
        self.extra_headers = cfg.extra_headers.copy() if cfg.extra_headers else {}

    def __str__(self):
        return f"{self.__class__.__name__}"

    @property
    @abstractmethod
    def default_params(self) -> dict:
        raise NotImplementedError

    @property
    @abstractmethod
    def default_model(self) -> str:
        raise NotImplementedError


from app.utils.logger import get_logger


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, base_url: str):
        super().__init__(api_key, base_url)
        self.logger = get_logger(__name__)

    @property
    @abstractmethod
    def client(self) -> OpenAI:
        raise NotImplementedError

    def ask(
            self,
            messages: list[dict],
            model: Optional[str] = None,
            params: Optional[dict] = None,
            *args, **kwargs
    ) -> ChatCompletionMessage:
        llm_params = self.default_params.copy()
        if params:
            llm_params.update(params)

        if not model:
            model = self.default_model

        self.logger.info(f"Отправляем запрос к модели: {model}")
        if s.mode == 'dev':
            self.logger.info(f"Параметры модели: {llm_params}")
            self.logger.info(f"messages:\n{messages}")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                extra_headers=self.extra_headers,
                *args,
                **kwargs,
                **llm_params,
            )
            self.logger.info(f"Успешно получен ответ от модели: {model}")
        except OpenAIError as e:
            self.logger.error(f"❌ Ошибка модели: '{model}': {e}")
            raise e

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls":
            self.logger.info(f"Запрос на вызов функций 'function calling'")
        else:
            self.logger.info(f"Обычное текстовое сообщение")
            choice.message.content = clean_model_response(choice.message.content)

        if s.mode == 'dev':
            self.logger.info(choice)

        return choice.message


class OpenAIEmbeddingProvider(BaseLLMProvider):
    def __init__(self, api_key: str, base_url: str):
        super().__init__(api_key, base_url)
        self.logger = get_logger(__name__)

    @property
    @abstractmethod
    def embedding_model(self) -> str:
        return NotImplemented

    @property
    @abstractmethod
    def embedding_column(self) -> str:
        return NotImplemented

    @property
    @abstractmethod
    def client(self) -> OpenAI:
        return NotImplemented

    def vectorize(self, query: str, model: str = None) -> EmbeddingResult:
        embedding_model = self.embedding_model if not model else model

        self.logger.info(f"Отправляем запрос к модели: {embedding_model}")
        self.logger.info(f'Векторизируем вопрос пользователя:\n{query}')

        embedding_params = {
            "model": embedding_model,
            "input": query,
            "extra_headers": self.extra_headers
        }
        try:
            response = self.client.embeddings.create(**embedding_params)
            self.logger.info(f"Успешно получен ответ от модели: {embedding_model}")
        except OpenAIError as e:
            self.logger.error(f"❌ ошибка модели: '{embedding_model}': {e}")
            raise

        embedding = response.data[0].embedding
        return EmbeddingResult(vector=embedding, column=self.embedding_column)
