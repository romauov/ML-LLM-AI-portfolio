import json
import time
from typing import Any, Dict, List, Union, Literal, Optional, Tuple

from pydantic import BaseModel, model_validator


class ContentImageUrl(BaseModel):
    type: str = "image_url"
    image_url: str


class SubmitRequest(BaseModel):
    message: str | None = None
    dialog_history: list[dict[str, str]] | None = None
    file_path: str | None = None


class ContentText(BaseModel):
    type: str = "text"
    text: str


class Dialog(BaseModel):
    role: Literal["user", "assistant", "bot"]
    content: Union[str, Tuple[ContentText, ContentImageUrl]]


class DialogHistory(BaseModel):
    dialog: Optional[List[Dialog]] = None

    @model_validator(mode='before')
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value




class ChatCompletionMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "INLINE Vet-bot"
    messages: List[ChatCompletionMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatCompletionMessage
    finish_reason: str = "stop"


class ChatCompletionResponseUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: ChatCompletionResponseUsage


class ChatCompletionStreamChoice(BaseModel):
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[str] = None


class ChatCompletionStream(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionStreamChoice]


class ModelCard(BaseModel):
    id: str
    object: str = "model"
    created: int = int(time.time())
    owned_by: str = "agro-vet-ai"


class ModelList(BaseModel):
    object: str = "list"
    data: List[ModelCard]
