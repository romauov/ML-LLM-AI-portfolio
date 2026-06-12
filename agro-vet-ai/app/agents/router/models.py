from pydantic import BaseModel


class TopicRouterAgentResponse(BaseModel):
    response: str
    context: str = ""
    context_images: list[str] = []
    file_requests: list[dict] = None