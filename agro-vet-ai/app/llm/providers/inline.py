from openai import OpenAI

from config.config import Config
from app.llm.providers.base import OpenAIProvider
from app.utils.logger import get_logger


class InlineProvider(OpenAIProvider):
    def __init__(self, api_key: str, base_url: str):
        super().__init__(api_key, base_url)
        self.logger = get_logger(__name__)

        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.cfg = Config.from_yaml()
        self._default_params = self.cfg.llm_hyperparameters.inline.dict()
        self._default_model = self.cfg.llm_models.inline.llm

    @property
    def client(self) -> OpenAI:
        return self._client

    @property
    def default_params(self) -> dict:
        return self._default_params

    @property
    def default_model(self) -> str:
        return self._default_model
