"""
LLM провайдеры для DeepEval тестов

Поддерживаемые провайдеры:
- DeepSeek: DeepSeek API (deepseek-chat, deepseek-reasoner)
- VseGPT: VseGPT API через OpenAI-совместимый интерфейс
- OpenRouter: OpenRouter API через OpenAI-совместимый интерфейс
- Local: Локальная модель через OpenAI-совместимый интерфейс
"""
import sys
from enum import Enum
from typing import Optional, Union
from pathlib import Path
from pydantic import BaseModel

from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.models.llms.deepseek_model import DeepSeekModel
from app.utils.settings import secrets as s

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class ProviderType(Enum):
    """Типы поддерживаемых провайдеров"""
    DEEPSEEK = "deepseek"
    VSEGPT = "vsegpt"
    OPENROUTER = "openrouter"
    LOCAL = "local"


class DeepSeekProvider(DeepEvalBaseLLM):
    """
    DeepSeek API провайдер

    Использует встроенный DeepSeekModel из DeepEval

    Args:
        model: Название модели (по умолчанию "deepseek-chat")
        api_key: API ключ (берется из DEEPSEEK_API_KEY если не указан)
        base_url: Base URL (опционально, для совместимости с фабрикой)
    """

    def __init__(
        self,
        model: str = "deepseek-chat",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.model_name = model

        # DeepSeekModel поддерживает только model, api_key, и temperature
        # base_url игнорируется (не поддерживается встроенной моделью)
        self.provider = DeepSeekModel(
            model=model,
            api_key=api_key or s.deepseek_api_key,
            temperature=0
        )

    def load_model(self):
        return self.provider

    def generate(self, prompt: str, schema: Optional[BaseModel] = None) -> Union[str, BaseModel]:
        result, _ = self.provider.generate(prompt, schema)
        return result

    async def a_generate(self, prompt: str, schema: Optional[BaseModel] = None) -> Union[str, BaseModel]:
        result, _ = await self.provider.a_generate(prompt, schema)
        return result

    def get_model_name(self) -> str:
        return f"DeepSeek ({self.model_name})"


class VseGPTProvider(DeepEvalBaseLLM):
    """
    VseGPT API провайдер

    Args:
        model: Название модели
        api_key: API ключ (берется из VSEGPT_API_KEY если не указан)
        base_url: Base URL (берется из VSEGPT_BASE_URL если не указан)
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        from openai import OpenAI
        from config.config import Config

        cfg = Config.from_yaml()
        self.model_name = model or cfg.llm_models.vsegpt.llm
        self.client = OpenAI(
            api_key=api_key or s.vsegpt_api_key,
            base_url=base_url or s.vsegpt_base_url
        )

    def load_model(self):
        return self  # type: ignore

    def generate(self, prompt: str, schema: Optional[BaseModel] = None) -> Union[str, BaseModel]:
        messages = [{"role": "user", "content": prompt}]  # type: ignore

        # Детерминистичные параметры генерации
        generation_params = {
            "temperature": 0,
            "top_p": 1.0,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "seed": 42
        }

        if schema:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,  # type: ignore
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "schema": schema.model_json_schema(),
                        "strict": False
                    }
                },
                **generation_params
            )
            content = response.choices[0].message.content or ""
            return schema.model_validate_json(content)
        else:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,  # type: ignore
                **generation_params
            )
            return response.choices[0].message.content or ""

    async def a_generate(self, prompt: str, schema: Optional[BaseModel] = None) -> Union[str, BaseModel]:
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.generate, prompt, schema)

    def get_model_name(self) -> str:
        return f"VseGPT ({self.model_name})"


class OpenRouterProvider(DeepEvalBaseLLM):
    """OpenRouter API провайдер"""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None):
        from openai import OpenAI
        from config.config import Config
        import logging

        cfg = Config.from_yaml()
        self.model_name = model or cfg.llm_models.openrouter.llm
        self.logger = logging.getLogger(__name__)
        self.client = OpenAI(
            api_key=api_key or s.openrouter_api_key,
            base_url=base_url or s.openrouter_base_url
        )

    def load_model(self):
        return self  # type: ignore

    def generate(self, prompt: str, schema: Optional[BaseModel] = None):
        messages = [{"role": "user", "content": prompt}]  # type: ignore

        # Детерминистичные параметры генерации
        generation_params = {
            "temperature": 0,
            "top_p": 1.0,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "seed": 42
        }

        if schema:
            response = None
            try:
                # OpenRouter doesn't support json_schema for most models
                # Use JSON mode instead and add schema to the prompt
                import json
                schema_str = json.dumps(schema.model_json_schema(), indent=2)
                enhanced_prompt = f"""{prompt}

Please respond with valid JSON that matches this schema:
{schema_str}

Respond ONLY with valid JSON, no additional text."""

                enhanced_messages = [{"role": "user", "content": enhanced_prompt}]  # type: ignore

                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=enhanced_messages,  # type: ignore
                    response_format={"type": "json_object"},
                    **generation_params
                )
                content = response.choices[0].message.content or ""
                self.logger.debug(f"OpenRouter structured response: {content[:200]}...")
                return schema.model_validate_json(content)
            except Exception as e:
                self.logger.error(f"OpenRouter structured output failed: {e}")
                if response:
                    self.logger.error(f"Response content: {response.choices[0].message.content}")
                raise

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,  # type: ignore
            **generation_params
        )
        return response.choices[0].message.content or ""

    async def a_generate(self, prompt: str, schema: Optional[BaseModel] = None):
        import asyncio
        return await asyncio.get_running_loop().run_in_executor(None, self.generate, prompt, schema)

    def get_model_name(self) -> str:
        return f"OpenRouter ({self.model_name})"


class LocalProvider(DeepEvalBaseLLM):
    """Локальная модель провайдер (LM Studio)"""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None):
        from openai import OpenAI
        from config.config import Config

        cfg = Config.from_yaml()
        self.model_name = model or cfg.llm_models.inline.llm
        self.client = OpenAI(
            api_key=api_key or s.inline_api_key,
            base_url=base_url or s.inline_base_url
        )

    def load_model(self):
        return self  # type: ignore

    def generate(self, prompt: str, schema: Optional[BaseModel] = None):
        messages = [{"role": "user", "content": prompt}]  # type: ignore

        # Детерминистичные параметры генерации (для LM Studio)
        generation_params = {
            "temperature": 0.0,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "seed": 42
        }

        if schema:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,  # type: ignore
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "schema": schema.model_json_schema(),
                        "strict": False
                    }
                },
                **generation_params
            )
            return schema.model_validate_json(response.choices[0].message.content or "")

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,  # type: ignore
            **generation_params
        )
        return response.choices[0].message.content or ""

    async def a_generate(self, prompt: str, schema: Optional[BaseModel] = None):
        import asyncio
        return await asyncio.get_running_loop().run_in_executor(None, self.generate, prompt, schema)

    def get_model_name(self) -> str:
        return f"Local ({self.model_name})"


class ProviderFactory:
    """Фабрика для создания LLM провайдеров"""

    @staticmethod
    def create_provider(provider_type: Union[ProviderType, str], model: Optional[str] = None, **kwargs) -> DeepEvalBaseLLM:
        if isinstance(provider_type, str):
            provider_type = ProviderType(provider_type.lower())

        if provider_type == ProviderType.DEEPSEEK:
            return DeepSeekProvider(model=model or "deepseek-chat", **kwargs)
        elif provider_type == ProviderType.VSEGPT:
            return VseGPTProvider(model=model, **kwargs)
        elif provider_type == ProviderType.OPENROUTER:
            return OpenRouterProvider(model=model, **kwargs)
        elif provider_type == ProviderType.LOCAL:
            return LocalProvider(model=model, **kwargs)

        raise ValueError(f"Неподдерживаемый провайдер: {provider_type}")

    @staticmethod
    def from_config(config: dict) -> DeepEvalBaseLLM:
        provider_type = config.get("provider")
        if not provider_type:
            raise ValueError("Конфигурация должна содержать ключ 'provider'")

        return ProviderFactory.create_provider(
            provider_type=provider_type,
            model=config.get("model"),
            api_key=config.get("api_key"),
            base_url=config.get("base_url")
        )
