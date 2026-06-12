"""LLM client configuration and factory for creating ChatOpenAI instances with X-title header."""
import logging
from langchain_openai import ChatOpenAI
from app.config import Settings
from typing import Dict, Optional, List, Union, Any, Iterator
from langchain_core.runnables import Runnable


logger = logging.getLogger(__name__)

# class LLMClientFactory:
#     """Factory for creating LLM clients with X-title header."""

#     def __init__(self, settings: Settings):
#         """Initialize factory with settings.

#         Args:
#             settings: Application settings instance
#         """
#         self.settings = settings

#     def get_headers(self) -> Dict[str, str]:
#         """Get LLM headers with X-title.

#         Returns:
#             Dictionary of headers to include in LLM requests
#         """
#         # Return X-title header as specified in requirements
#         return {
#             "X-title": "agro-vet-ai"
#         }

#     def create_chat_llm(
#         self,
#         model: Optional[str] = None,
#         temperature: float = 0,
#         streaming: bool = True,
#     ) -> ChatOpenAI:
#         """Create ChatOpenAI instance with proper configuration.

#         Args:
#             model: Model name (defaults to settings.LLM_MODEL)
#             temperature: Temperature for generation (default 0 for deterministic)
#             streaming: Enable streaming responses (default True)

#         Returns:
#             Configured ChatOpenAI instance
#         """
#         # Use defaults from settings

#         headers = self.get_headers()

#         return ChatOpenAI(
#             base_url=self.settings.LLM_API_BASE,
#             api_key=self.settings.LLM_API_KEY,
#             model=model or self.settings.LLM_MODEL,
#             temperature=temperature,
#             streaming=streaming,
#             default_headers=headers,
#         )


"""LLM client configuration and factory for creating ChatOpenAI instances with X-title header."""


class FallbackLLM(Runnable):
    """Wrapper for LLM with fallback support across providers."""

    def __init__(self, llms: List[ChatOpenAI], allow_fallbacks: bool = True):
        self.llms = llms
        self.allow_fallbacks = allow_fallbacks
        self.current_provider_index = 0

    @property
    def _llm(self) -> ChatOpenAI:
        """Get current LLM instance."""
        return self.llms[self.current_provider_index]

    def invoke(self, *args, **kwargs) -> Any:
        """Invoke LLM with fallback support."""
        last_error = None

        for i, llm in enumerate(self.llms):
            try:
                if i == self.current_provider_index:
                    logger.info(f"Using provider index: {i}")
                    result = llm.invoke(*args, **kwargs)
                    return result
            except Exception as e:
                last_error = e
                logger.warning(f"Provider at index {i} failed: {str(e)[:200]}")

                if not self.allow_fallbacks:
                    break

                # Try next provider
                if i < len(self.llms) - 1:
                    logger.info(f"Falling back to next provider")
                    self.current_provider_index = i + 1
                    continue
                else:
                    break

        # If we get here, all providers failed
        error_msg = "All LLM providers failed"
        if last_error:
            error_msg += f". Last error: {str(last_error)[:200]}"
        raise Exception(error_msg)

    def stream(self, *args, **kwargs) -> Iterator[Any]:
        """Stream LLM response with fallback support."""
        last_error = None

        for i, llm in enumerate(self.llms):
            try:
                if i == self.current_provider_index:
                    logger.info(f"Streaming with provider index: {i}")
                    return llm.stream(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Provider at index {i} failed during stream: {str(e)[:200]}")

                if not self.allow_fallbacks:
                    break

                # Try next provider
                if i < len(self.llms) - 1:
                    logger.info(f"Falling back to next provider for streaming")
                    self.current_provider_index = i + 1
                    continue
                else:
                    break

        # If we get here, all providers failed
        error_msg = "All LLM providers failed during streaming"
        if last_error:
            error_msg += f". Last error: {str(last_error)[:200]}"
        raise Exception(error_msg)

    def bind_tools(self, tools, **kwargs):
        """Bind tools to the LLM - delegates to current LLM."""
        return self._llm.bind_tools(tools, **kwargs)

    def bind(self, **kwargs):
        """Bind additional arguments to the LLM - delegates to current LLM."""
        return self._llm.bind(**kwargs)

    # Add compatibility methods for agent creation
    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to current LLM."""
        return getattr(self._llm, name)


class LLMClientFactory:
    """Factory for creating LLM clients with X-title header and provider fallback."""

    def __init__(self, settings: Settings):
        """Initialize factory with settings.

        Args:
            settings: Application settings instance
        """
        self.settings = settings
        self._provider_models = self._load_provider_models()

    def _load_provider_models(self) -> Dict[str, str]:
        """Load provider to model mapping.

        Returns:
            Dictionary mapping provider names to model names
        """
        # Get custom model mapping from settings or use defaults
        # default_mapping = {
        #     "friendli": "minimax/minimax-m2.1",
        #     "deepinfra/fp8": "minimax/minimax-m2.1",
        #     "nebius/fp8": "minimax/minimax-m2.1",
        # }
        default_mapping = {
            # "google-vertex": "minimax/minimax-m2",
            # "deepinfra/fp8": "minimax/minimax-m2",
            # "minimax/fp8": "minimax/minimax-m2",
        }
        # default_mapping = {
        #     "hyperbolic/bf16": "qwen/qwen3-next-80b-a3b-thinking",
        #     "together": "qwen/qwen3-next-80b-a3b-thinking",
        #     "google-vertex": "qwen/qwen3-next-80b-a3b-thinking",
        #     "nebius/fp8": "qwen/qwen3-next-80b-a3b-thinking"
        # }
        # default_mapping = {
        #     "google-vertex": "google/gemini-2.5-flash-lite",
        #     "google-ai-studio": "google/gemini-2.5-flash-lite"
        # }

        if hasattr(self.settings, 'LLM_PROVIDER_MODEL_MAP'):
            default_mapping.update(self.settings.LLM_PROVIDER_MODEL_MAP)

        return default_mapping

    def get_headers(self) -> Dict[str, str]:
        """Get LLM headers with X-title.

        Returns:
            Dictionary of headers to include in LLM requests
        """
        headers = {
            "X-title": "agro-vet-ai",
            "HTTP-Referer": getattr(self.settings, 'APP_URL', 'https://agro-vet-ai.app'),
        }

        # Add optional X-Title for specific providers if needed
        if hasattr(self.settings, 'LLM_X_TITLE'):
            headers["X-Title"] = self.settings.LLM_X_TITLE

        return headers

    def create_basic_chat_llm(
        self,
        model: Optional[str] = None,
        temperature: float = 0,
        streaming: bool = True,
        **kwargs
    ) -> ChatOpenAI:
        """Create a basic ChatOpenAI instance without fallback logic.

        This is used for agent creation where bind() method is required.

        Args:
            model: Model name (defaults to first available model from provider mapping)
            temperature: Temperature for generation
            streaming: Enable streaming responses
            **kwargs: Additional arguments for ChatOpenAI

        Returns:
            Configured ChatOpenAI instance
        """
        headers = self.get_headers()

        # Use provided model, or first available model from provider mapping, or fall back to settings.LLM_MODEL
        final_model = model
        if final_model is None and self._provider_models:
            # Use the first model from provider mapping as default
            final_model = next(iter(self._provider_models.values()))
        elif final_model is None:
            # Fallback to settings.LLM_MODEL if no provider models available
            final_model = self.settings.LLM_MODEL

        return ChatOpenAI(
            base_url=self.settings.LLM_API_BASE,
            api_key=self.settings.LLM_API_KEY,
            model=final_model,
            temperature=temperature,
            streaming=streaming,
            default_headers=headers,
            **kwargs
        )

    def create_chat_llm_for_provider(
        self,
        provider: str,
        model: Optional[str] = None,
        temperature: float = 0,
        streaming: bool = True,
        **kwargs
    ) -> ChatOpenAI:
        """Create ChatOpenAI instance for a specific provider.

        Args:
            provider: Provider name from LLM_PROVIDER_ORDER
            model: Model name (defaults to provider-specific model from mapping)
            temperature: Temperature for generation
            streaming: Enable streaming responses
            **kwargs: Additional arguments for ChatOpenAI

        Returns:
            Configured ChatOpenAI instance
        """
        # Get model for provider or use provided model
        if model is None:
            # Only use models from _load_provider_models mapping
            if provider in self._provider_models:
                model = self._provider_models[provider]
            else:
                # If provider is not in the mapping, raise an exception
                raise ValueError(f"Provider '{provider}' not found in provider model mapping. "
                                 f"Available providers: {list(self._provider_models.keys())}")

        # Get provider-specific API base if configured, otherwise use default
        api_base = getattr(self.settings, 'LLM_API_BASE',
                           "https://openrouter.ai/api/v1")

        # Get provider-specific API key if configured, otherwise use default
        api_key = getattr(self.settings, 'LLM_API_KEY', None)

        headers = self.get_headers()

        # Add provider-specific headers if needed
        if hasattr(self.settings, 'LLM_ADDITIONAL_HEADERS'):
            headers.update(self.settings.LLM_ADDITIONAL_HEADERS)

        logger.debug(
            f"Creating LLM for provider '{provider}' with model '{model}'")

        return ChatOpenAI(
            base_url=api_base,
            api_key=api_key,
            model=model,
            temperature=temperature,
            streaming=streaming,
            default_headers=headers,
            **kwargs
        )

    def create_chat_llm(
        self,
        model: Optional[str] = None,
        temperature: float = 0,
        streaming: bool = True,
        provider_order: Optional[List[str]] = None,
        allow_fallbacks: Optional[bool] = None,
        use_for_agent: bool = False,
        **kwargs
    ) -> Union[ChatOpenAI, FallbackLLM]:
        """Create ChatOpenAI instance with proper configuration and fallback support.

        Args:
            model: Model name (defaults to first available model from provider mapping)
            temperature: Temperature for generation (default 0 for deterministic)
            streaming: Enable streaming responses (default True)
            provider_order: List of providers to try in order
            allow_fallbacks: Whether to allow fallback between providers
            use_for_agent: Set to True if LLM will be used for agent creation
            **kwargs: Additional arguments for ChatOpenAI

        Returns:
            Configured ChatOpenAI instance or FallbackLLM wrapper
        """
        # If LLM will be used for agent creation, use basic implementation
        # because agents require bind() method
        if use_for_agent:
            logger.info(
                "Creating basic LLM for agent use (fallbacks disabled for agents)")
            return self.create_basic_chat_llm(
                model=model,
                temperature=temperature,
                streaming=streaming,
                **kwargs
            )

        # Get provider configuration from settings or use defaults
        if provider_order is None:
            provider_order = getattr(
                self.settings,
                'LLM_PROVIDER_ORDER',
                # Use providers from _load_provider_models
                list(self._provider_models.keys())
            )

        if allow_fallbacks is None:
            allow_fallbacks = getattr(
                self.settings, 'LLM_ALLOW_FALLBACKS', True)

        # If only one provider or fallbacks disabled, create simple ChatOpenAI
        if len(provider_order) == 1 or not allow_fallbacks:
            provider = provider_order[0]
            return self.create_chat_llm_for_provider(
                provider=provider,
                model=model,
                temperature=temperature,
                streaming=streaming,
                **kwargs
            )

        # Create multiple LLMs for fallback support
        llms = []
        for provider in provider_order:
            llm = self.create_chat_llm_for_provider(
                provider=provider,
                model=model,
                temperature=temperature,
                streaming=streaming,
                **kwargs
            )
            llms.append(llm)

        logger.info(
            f"Created fallback LLM with {len(provider_order)} providers")
        return FallbackLLM(llms, allow_fallbacks=allow_fallbacks)

    def get_model_for_agent(self, model: Optional[str] = None) -> str:
        """Get the model name that would be used for an agent.

        This method allows retrieving the actual model that would be used
        by an agent, which comes from the provider mapping.

        Args:
            model: Optional model name to use

        Returns:
            Model name that would be used
        """
        if model:
            return model

        # Use first available model from provider mapping
        if self._provider_models:
            return next(iter(self._provider_models.values()))

        # Fallback to settings.LLM_MODEL
        return getattr(self.settings, 'LLM_MODEL', "")
