import asyncio
import time
import uuid

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse

from app.agents.factory import get_agent
from app.web_api.models import (
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatCompletionResponseUsage,
    ModelCard,
    ModelList,
)
from app.web_api.text_formatter import format_to_markdown
from app.web_api.auth import verify_api_key
from app.web_api.streaming import stream_response

openai_router = APIRouter()


@openai_router.post("/v1/chat/completions")
async def chat_completions(
    body: ChatCompletionRequest,
    api_key: str = Depends(verify_api_key),
    http_request: Request = None,
):
    """Совместимая с OpenAI API точка доступа с поддержкой стриминга."""
    try:
        user_message = ""
        for msg in reversed(body.messages):
            if msg.role == "user":
                user_message = msg.content
                break

        if body.messages and body.messages[-1].role == "user":
            dialog_history = [m.dict() for m in body.messages[:-1]]
        else:
            dialog_history = [m.dict() for m in body.messages]

        request_id = f"chatcmpl-{uuid.uuid4().hex}"
        created = int(time.time())

        if body.stream and body.model == "INLINE Vet-bot Test":
            agent_router = get_agent(model=body.model, dialog_history=dialog_history)
            return StreamingResponse(
                stream_response(
                    agent=agent_router,
                    question=user_message,
                    request_id=request_id,
                    created=created,
                    model_name=body.model,
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        agent_router = get_agent(model=body.model, dialog_history=dialog_history)
        response = await asyncio.to_thread(agent_router.process, question=user_message)
        formatted_response_text = format_to_markdown(response.response)

        response_id = f"chatcmpl-{uuid.uuid4().hex}"
        current_time = int(time.time())

        response = ChatCompletionResponse(
            id=response_id,
            created=current_time,
            model=body.model,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant", content=formatted_response_text
                    ),
                )
            ],
            usage=ChatCompletionResponseUsage(
                prompt_tokens=len(user_message),
                completion_tokens=len(formatted_response_text),
                total_tokens=len(user_message) + len(formatted_response_text),
            ),
        )

        return response

    except Exception as e:
        print(f"Error in chat_completions: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@openai_router.get("/v1/models", response_model=ModelList)
async def get_models(api_key: str = Depends(verify_api_key)):
    """Возвращает список доступных моделей."""
    models = [ModelCard(id="INLINE Vet-bot"), ModelCard(id="INLINE Vet-bot Test")]
    return ModelList(data=models)
