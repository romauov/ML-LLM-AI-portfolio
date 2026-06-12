import os.path
from typing import Dict, Optional

from omegaconf import OmegaConf
from pydantic import BaseModel


class Search(BaseModel, extra='allow'):
    doc_limit: int
    similarity_threshold: float


class Rag(BaseModel, extra='allow'):
    search: Search


class Hyperparameters(BaseModel, extra='allow'):
    temperature: float
    top_p: float
    max_tokens: int
    frequency_penalty: float
    presence_penalty: float


class LibrarianAgent(BaseModel, extra='allow'):
    llm_hyperparameters: Hyperparameters
    max_attempts: int


class Librarian(BaseModel, extra='allow'):
    main_agent: LibrarianAgent
    search: Search


class PharmacistSearch(BaseModel, extra='allow'):
    chunk_limit: int
    similarity_threshold: float
    overflow_threshold: int = 5


class PharmacistAgent(BaseModel, extra='allow'):
    llm_hyperparameters: Hyperparameters
    max_attempts: int


class Pharmacist(BaseModel, extra='allow'):
    main_agent: PharmacistAgent
    search: PharmacistSearch


class RouterAgent(BaseModel, extra='allow'):
    llm_hyperparameters: Hyperparameters
    max_attempts: int


class LLMHyperparameters(BaseModel, extra='allow'):
    inline: Hyperparameters
    vsegpt: Hyperparameters


class LLMModelsProvider(BaseModel, extra='allow'):
    llm: Optional[str] = None
    embedding: Optional[str] = None
    embedding_column: Optional[str] = None
    embedding_query_instruction: Optional[str] = None


class LLMModels(BaseModel, extra='allow'):
    inline: LLMModelsProvider
    vsegpt: LLMModelsProvider
    openrouter: LLMModelsProvider
    tool_model: str
    evaluation_model: str
    ocr_model: str


class Config(BaseModel, extra='allow'):
    count_history_messages: int
    max_file_size_mb: int
    max_filtered_topics: int
    rag: Rag
    librarian: Librarian
    pharmacist: Pharmacist
    router_agent: RouterAgent  # Added router_agent configuration
    llm_hyperparameters: LLMHyperparameters
    llm_models: LLMModels
    extra_headers: Dict[str, str]

    @classmethod
    def from_yaml(cls) -> 'Config':
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.yaml')
        cfg = OmegaConf.to_container(OmegaConf.load(path), resolve=True)
        return cls(**cfg)
