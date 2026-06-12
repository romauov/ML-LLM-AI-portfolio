import json
from typing import AsyncGenerator

from app.web_api.models import (
    ChatCompletionStream,
    ChatCompletionStreamChoice,
)
from app.web_api.text_formatter import format_to_markdown


async def stream_response(
    agent,
    question: str,
    request_id: str,
    created: int,
    model_name: str,
) -> AsyncGenerator[str, None]:
    """Потоковая передача ответа агента в формате OpenAI (SSE)."""
    try:
        async for event in agent.process_stream(question):
            if "error" in event:
                error_chunk = ChatCompletionStream(
                    id=request_id,
                    created=created,
                    model=model_name,
                    choices=[
                        ChatCompletionStreamChoice(
                            index=0,
                            delta={"content": f"\n\n[Error: {event['error']}]"},
                            finish_reason="error",
                        )
                    ],
                )
                yield f"data: {error_chunk.model_dump_json()}\n\n"
                yield "data: [DONE]\n\n"
                return

            node = event.get("node", "")

            if node == "llm_stream":
                content = event.get("data", {}).get("content", "")
                if content:
                    chunk = ChatCompletionStream(
                        id=request_id,
                        created=created,
                        model=model_name,
                        choices=[
                            ChatCompletionStreamChoice(
                                index=0, delta={"content": content}, finish_reason=None
                            )
                        ],
                    )
                    yield f"data: {chunk.model_dump_json()}\n\n"

            elif node == "tool_start":
                tool_name = event.get("data", {}).get("tool", "")
                tool_input = event.get("data", {}).get("input", {})
                run_id = event.get("data", {}).get("run_id", "unknown")[:8]
                tool_chunk = ChatCompletionStream(
                    id=request_id,
                    created=created,
                    model=model_name,
                    choices=[
                        ChatCompletionStreamChoice(
                            index=0,
                            delta={
                                "tool_calls": [
                                    {
                                        "id": f"call_{run_id}",
                                        "type": "function",
                                        "function": {
                                            "name": tool_name,
                                            "arguments": json.dumps(
                                                tool_input, ensure_ascii=False
                                            ),
                                        },
                                    }
                                ]
                            },
                            finish_reason=None,
                        )
                    ],
                )
                yield f"data: {tool_chunk.model_dump_json()}\n\n"

            elif node == "tool_end":
                summary = event.get("data", {}).get("summary", "")
                if summary:
                    tool_end_chunk = ChatCompletionStream(
                        id=request_id,
                        created=created,
                        model=model_name,
                        choices=[
                            ChatCompletionStreamChoice(
                                index=0,
                                delta={"content": f"\n{summary}\n"},
                                finish_reason=None,
                            )
                        ],
                    )
                    yield f"data: {tool_end_chunk.model_dump_json()}\n\n"

            elif node == "final_output":
                content = event.get("data", {}).get("content", "")
                if content:
                    formatted = format_to_markdown(content)
                    final_content_chunk = ChatCompletionStream(
                        id=request_id,
                        created=created,
                        model=model_name,
                        choices=[
                            ChatCompletionStreamChoice(
                                index=0,
                                delta={"content": f"\n{formatted}"},
                                finish_reason=None,
                            )
                        ],
                    )
                    yield f"data: {final_content_chunk.model_dump_json()}\n\n"

        final_chunk = ChatCompletionStream(
            id=request_id,
            created=created,
            model=model_name,
            choices=[
                ChatCompletionStreamChoice(index=0, delta={}, finish_reason="stop")
            ],
        )
        yield f"data: {final_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        error_chunk = ChatCompletionStream(
            id=request_id,
            created=created,
            model=model_name,
            choices=[
                ChatCompletionStreamChoice(
                    index=0,
                    delta={"content": f"\n\n[Error: {str(e)}]"},
                    finish_reason="error",
                )
            ],
        )
        yield f"data: {error_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
