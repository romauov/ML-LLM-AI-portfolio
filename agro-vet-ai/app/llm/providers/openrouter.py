from openai import OpenAI

from config.config import Config

from app.llm.providers.base import OpenAIProvider, OpenAIEmbeddingProvider
from app.utils.logger import get_logger


class OpenrouterProvider(OpenAIProvider, OpenAIEmbeddingProvider):
    def __init__(self, api_key: str, base_url: str):
        super().__init__(api_key, base_url)
        self.logger = get_logger(__name__)

        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.cfg = Config.from_yaml()
        self._default_params = self.cfg.llm_hyperparameters.vsegpt.dict()
        self._default_model = self.cfg.llm_models.openrouter.llm

        self._embedding_model = self.cfg.llm_models.openrouter.embedding
        self._embedding_column = self.cfg.llm_models.openrouter.embedding_column

    @property
    def client(self) -> OpenAI:
        return self._client

    @property
    def default_params(self) -> dict:
        return self._default_params

    @property
    def default_model(self) -> str:
        return self._default_model

    @property
    def embedding_model(self) -> str:
        return self._embedding_model

    @property
    def embedding_column(self) -> str:
        return self._embedding_column

    def vectorize(self, query: str, model: str = None) -> "EmbeddingResult":
        instruction = self.cfg.llm_models.openrouter.embedding_query_instruction
        if instruction:
            query = instruction + query
        return super().vectorize(query=query, model=model)
