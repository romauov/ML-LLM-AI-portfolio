from typing import Optional

from openai.types.chat import ChatCompletionMessage

from app.llm.providers.base import EmbeddingResult
from app.llm.providers.inline import InlineProvider
from app.llm.providers.openrouter import OpenrouterProvider
from app.llm.providers.vsegpt import VseGPTProvider
from app.utils.logger import get_logger
from app.utils.settings import secrets as s
from app.utils.singleton import Singleton
from config.config import Config


class LLMProvider(metaclass=Singleton):
    def __init__(self):
        self.logger = get_logger(__name__)
        self.cfg = Config.from_yaml()
        self._providers = [
            {
                'instance': OpenrouterProvider,
                'args': {
                    'api_key': s.openrouter_api_key,
                    'base_url': s.openrouter_base_url
                }
            },
            {
                'instance': VseGPTProvider,
                'args': {
                    'api_key': s.vsegpt_api_key,
                    'base_url': s.vsegpt_base_url
                }
            },
            {
                'instance': InlineProvider,
                'args': {
                    'api_key': s.inline_api_key,
                    'base_url': s.inline_base_url
                }
            }
        ]

        self.allowed_providers = []
        for data in self._providers:
            provider = data['instance']
            provider_args = data['args']

            if not provider_args['api_key'] or not provider_args['base_url']:
                self.logger.warning(f'Не заданы api_key или base_url для провайдера {provider}. '
                                    f'Провайдер не инициализирован')
            else:
                provider_instance = provider(**provider_args)
                self.allowed_providers.append(provider_instance)
                self.logger.info(f"Успешно инициализирован провайдер: {provider_instance}")

        if not self.allowed_providers:
            raise ValueError("Не удалось инициализировать хотя бы 1 LLM провайдер")

    def ask(
            self,
            messages: list[dict],
            model: Optional[str] = None,
            params: Optional[dict] = None,
            *args, **kwargs
    ) -> ChatCompletionMessage:
        for provider in self.allowed_providers:
            try:
                self.logger.info(f"Обработка вопроса провайдером {provider}")
                response = provider.ask(
                    messages=messages,
                    model=model,
                    params=params,
                    *args, **kwargs,
                )
                return response
            except Exception as e:
                self.logger.info(f"Ошибка при попытке задать вопрос провайдеру {provider}. \n{e}")

        self.logger.info("Не удалось получить ответ от провайдеров")
        content = "Извините, в данный момент все сервера обработки запросов недоступны. Пожалуйста, попробуйте позже."
        return ChatCompletionMessage(content=content, role="assistant")

    def vectorize(
            self,
            query: str,
            model: str = None,
    ) -> EmbeddingResult:
        for provider in self.allowed_providers:
            if hasattr(provider, 'vectorize'):
                try:
                    self.logger.info(f"Векторизация запроса провайдером {provider}")
                    result = provider.vectorize(
                        query=query,
                        model=model,
                    )
                    return result
                except Exception as e:
                    self.logger.info(f"Ошибка при попытке векторизации провайдером {provider}. \n{e}")

        raise ValueError('Не удалось векторизовать запрос')
