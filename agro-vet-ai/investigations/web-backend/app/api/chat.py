"""LangServe API for veterinary agent - OpenAI-compatible chat completions endpoint."""

import json
import logging
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.agents import create_investigation_agent
from app.config import get_settings
from app.llm_config import LLMClientFactory
from app.services.mcp_client import VetRetroMCPClient
from app.services.investigation_manager import InvestigationManager
from app.auth import verify_api_key

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/v1", tags=["chat"])


# ============================================================================
# OpenAI-compatible request/response models
# ============================================================================

class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Optional name of the message author")


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: str = Field(default="investigations-swine", description="Model to use")
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    temperature: Optional[float] = Field(default=0.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(default=False, description="Whether to stream responses")
    investigation_id: Optional[str] = Field(None, description="Optional investigation ID for context")
    n: Optional[int] = Field(default=1, description="Number of completions to generate")
    stop: Optional[List[str]] = Field(None, description="Stop sequences")


class ChatCompletionChoice(BaseModel):
    """Single completion choice."""
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionUsage(BaseModel):
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None


class ChatCompletionChunk(BaseModel):
    """OpenAI-compatible streaming chunk."""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[Dict[str, Any]]


# ============================================================================
# Helper functions
# ============================================================================

def extract_investigation_id_from_history(messages: List[ChatMessage]) -> Optional[str]:
    """
    Extract investigation_id from chat history.

    Looks for the pattern: **Investigation ID:** `{investigation_id}`
    in assistant messages.
    """
    import re

    for msg in messages:
        if msg.role == "assistant" and "Investigation ID:" in msg.content:
            # Pattern: **Investigation ID:** `inv_20251117_123456_abc123`
            match = re.search(r'\*\*Investigation ID:\*\* `(inv_[^`]+)`', msg.content)
            if match:
                return match.group(1)
    return None


def generate_investigation_id() -> str:
    """
    Генерация уникального ID расследования.

    Формат: inv_random6
    Пример: inv_a3f8b2

    Примечание: Префикс "inv_" предотвращает интерпретацию ID как числа LLM-моделью
    """
    import secrets

    random_code = secrets.token_hex(3)  # 6 hex-символов
    return f"inv_{random_code}"


def convert_messages_to_langchain(messages: List[ChatMessage]) -> List[Any]:
    """Convert OpenAI-format messages to LangChain format."""
    lc_messages = []
    for msg in messages:
        if msg.role == "system":
            lc_messages.append(SystemMessage(content=msg.content))
        elif msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            lc_messages.append(AIMessage(content=msg.content))
    return lc_messages


def extract_user_input(messages: List[ChatMessage]) -> str:
    """Extract the last user message as input."""
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content
    return ""


def extract_chat_history(messages: List[ChatMessage]) -> List[Any]:
    """Extract chat history (all messages except the last user message)."""
    if len(messages) <= 1:
        return []

    history = []
    for msg in messages[:-1]:  # All except last
        if msg.role == "user":
            history.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            history.append(AIMessage(content=msg.content))
        elif msg.role == "system":
            history.append(SystemMessage(content=msg.content))

    return history


async def stream_agent_response(
    agent_executor,
    user_input: str,
    chat_history: List[Any],
    request_id: str,
    model_name: str,
    created: int,
    investigation_id: str,
    actual_model_used: str = "",
    is_new_investigation: bool = False,
    is_service_request: bool = False,
) -> AsyncGenerator[str, None]:
    """Потоковая передача ответа агента в формате OpenAI (SSE)."""
    try:
        # Отправляем Investigation ID и информацию о модели как первый чанк для нового расследования (но не для служебных запросов)
        if is_new_investigation and not is_service_request:
            # Формируем информационное сообщение с ID расследования и моделью
            # Use the actual model used, or fall back to settings.LLM_MODEL if not provided
            model_to_display = actual_model_used if actual_model_used else settings.LLM_MODEL
            info_message = (
                f"**Investigation ID:** `{investigation_id}`\n"
                f"**Model:** `{model_to_display}`\n\n"
            )
            id_chunk = ChatCompletionChunk(
                id=request_id,
                created=created,
                model=model_name,
                choices=[{
                    "index": 0,
                    "delta": {"content": info_message},
                    "finish_reason": None,
                }],
            )
            yield f"data: {id_chunk.model_dump_json()}\n\n"

        # Подготовка входных данных для агента
        agent_input = {
            "input": user_input,
        }

        if chat_history:
            agent_input["chat_history"] = chat_history

        # Потоковое выполнение агента
        async for event in agent_executor.astream_events(
            agent_input,
            version="v2",
            config=RunnableConfig(run_name="vet_agent_chat"),
        ):
            kind = event["event"]

            # Отладочное логирование всех событий
            logger.debug(f"Event: {kind} | Name: {event.get('name', 'N/A')}")

            # Логирование событий завершения цепочки для отладки
            if kind == "on_chain_end":
                logger.info(f"Chain ended: {event.get('name')} | Output keys: {list(event.get('data', {}).get('output', {}).keys() if isinstance(event.get('data', {}).get('output'), dict) else [])}")

            # Потоковая передача токенов LLM
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    chunk = ChatCompletionChunk(
                        id=request_id,
                        created=created,
                        model=model_name,
                        choices=[{
                            "index": 0,
                            "delta": {"content": content},
                            "finish_reason": None,
                        }],
                    )
                    yield f"data: {chunk.model_dump_json()}\n\n"

            # Отправка информации о вызове инструмента в UI
            elif kind == "on_tool_start":
                tool_name = event["name"]
                tool_input = event["data"].get("input", {})
                run_id = event.get("run_id", "unknown")

                logger.info(f"Tool called: {tool_name}")

                # Отправка начала вызова инструмента в OpenAI-совместимом формате
                # Позволяет UI типа Open WebUI отображать "Agent is thinking..."
                tool_call_chunk = ChatCompletionChunk(
                    id=request_id,
                    created=created,
                    model=model_name,
                    choices=[{
                        "index": 0,
                        "delta": {
                            "tool_calls": [{
                                "id": f"call_{run_id}",
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": json.dumps(tool_input, ensure_ascii=False)
                                }
                            }]
                        },
                        "finish_reason": None,
                    }],
                )
                yield f"data: {tool_call_chunk.model_dump_json()}\n\n"

            elif kind == "on_tool_error":
                tool_name = event["name"]
                error_data = event["data"]
                tool_input = error_data.get("input", {})
                error = error_data.get("error", "Unknown error")

                logger.error(f"Tool error: {tool_name} - {error}")

                # Create error message for user
                error_msg = f"❌ **Ошибка при вызове `{tool_name}`**: {str(error)}"

                # Send error as content chunk so user sees it
                error_chunk = ChatCompletionChunk(
                    id=request_id,
                    created=created,
                    model=model_name,
                    choices=[{
                        "index": 0,
                        "delta": {
                            "content": f"\n{error_msg}\n"
                        },
                        "finish_reason": None,
                    }],
                )
                yield f"data: {error_chunk.model_dump_json()}\n\n"

            elif kind == "on_tool_end":
                tool_name = event["name"]
                tool_output = event["data"].get("output", "")
                tool_input = event["data"].get("input", {})

                logger.info(f"Tool finished: {tool_name}")

                # Create informative summary based on tool type
                output_len = len(str(tool_output))

                # Format tool-specific summary
                if tool_name == "vet_search":
                    query = tool_input.get("query", "")[:50]
                    summary = f"🔍 **Поиск:** `{query}...` → {output_len} символов"
                elif tool_name == "get_pages":
                    source = tool_input.get("source_document", "")[:40]
                    pages = f"{tool_input.get('page_start', '?')}-{tool_input.get('page_end', '?')}"
                    summary = f"📄 **Получены страницы {pages}** из `{source}...` → {output_len} символов"
                elif tool_name == "vet_sources":
                    summary = f"📚 **Список источников** → {output_len} символов"
                elif tool_name == "source_info":
                    source = tool_input.get("source_document", "")[:40]
                    summary = f"📖 **Оглавление** для `{source}...` → {output_len} символов"
                elif tool_name == "todo_write":
                    # Parse todo list to show tasks
                    todos = tool_input.get("todos", [])

                    # Handle case where todos might be a JSON string
                    if isinstance(todos, str):
                        try:
                            todos = json.loads(todos)
                        except Exception:
                            todos = []

                    if todos and len(todos) > 0:
                        # Extract content from todos (dict or object)
                        task_contents = []
                        for t in todos[:3]:
                            if isinstance(t, dict):
                                content = t.get('content', 'Неизвестно')[:30]
                            else:
                                # TodoItem object
                                content = getattr(t, 'content', 'Неизвестно')[:30]
                            task_contents.append(f"'{content}...'")

                        tasks_summary = ", ".join(task_contents)
                        if len(todos) > 3:
                            tasks_summary += f" (+{len(todos)-3} ещё)"
                        summary = f"📝 **TODO обновлён:** {len(todos)} задач(и) - {tasks_summary}"
                    else:
                        summary = f"📝 **TODO обновлён** → {output_len} символов"
                # File tools
                elif tool_name == "create_investigation":
                    farm_name = tool_input.get("farm_name", "?")
                    problem_type = tool_input.get("problem_type", "?")
                    summary = f"📁 **Создано расследование** для фермы `{farm_name}` (тип: {problem_type})"
                elif tool_name == "list_investigations":
                    summary = f"📋 **Список расследований** → {output_len} символов"
                elif tool_name == "list_files":
                    # summary = f"📂 **Список файлов**"
                    summary = ""
                elif tool_name == "read_file":
                    filename = tool_input.get("filename", "?")
                    # summary = f"📖 **Прочитан файл** `{filename}`"
                    summary = ""  # Закомментировано для скрытия уведомления о чтении файла
                elif tool_name == "write_file":
                    filename = tool_input.get("filename", "?")
                    # summary = f"💾 **Записан файл** `{filename}`"
                    summary = ""  # Закомментировано для скрытия уведомления о записи файла
                elif tool_name == "append_to_file":
                    filename = tool_input.get("filename", "?")
                    # summary = f"➕ **Добавлено в файл** `{filename}`"
                    summary =""
                elif tool_name == "update_file_section":
                    filename = tool_input.get("filename", "?")
                    section = tool_input.get("section", "?")[:20]
                    # summary = f"✏️ **Обновлена секция** `{section}` в файле `{filename}`"
                    summary = ""  # Закомментировано для скрытия уведомления об обновлении секции
                elif tool_name == "get_instruction":
                    problem_type = tool_input.get("problem_type", "?")
                    type_names = {
                        "neonatal_diarrhea": "Неонатальная диарея",
                        "respiratory": "Респираторные проблемы",
                        "prrs": "РРСС"
                    }
                    type_display = type_names.get(problem_type, problem_type)
                    summary = f"📋 **Загружена инструкция:** {type_display} → {output_len} символов"
                else:
                    summary = f"🔧 **Инструмент `{tool_name}`** → {output_len} символов"

                result_chunk = ChatCompletionChunk(
                    id=request_id,
                    created=created,
                    model=model_name,
                    choices=[{
                        "index": 0,
                        "delta": {
                            "content": f"\n{summary}\n"
                        },
                        "finish_reason": None,
                    }],
                )
                yield f"data: {result_chunk.model_dump_json()}\n\n"
                

            # Handle final agent output (when early_stopping_method="generate")
            elif kind == "on_chain_end" and event.get("name") == "AgentExecutor":
                # Extract final output from agent
                output_data = event.get("data", {}).get("output", {})

                # AgentExecutor returns dict with 'output' key containing final answer
                if isinstance(output_data, dict):
                    final_output = output_data.get("output", "")
                else:
                    final_output = str(output_data)

                # Stream final output if it exists and hasn't been streamed yet
                # (This handles case when agent uses early_stopping_method="generate")
                if final_output and final_output.strip():
                    logger.info(f"Agent final output: {final_output[:100]}...")

                    # Stream the final answer as content
                    answer_chunk = ChatCompletionChunk(
                        id=request_id,
                        created=created,
                        model=model_name,
                        choices=[{
                            "index": 0,
                            "delta": {"content": f"\n\n{final_output}"},
                            "finish_reason": None,
                        }],
                    )
                    yield f"data: {answer_chunk.model_dump_json()}\n\n"

        # Send final chunk with finish_reason
        final_chunk = ChatCompletionChunk(
            id=request_id,
            created=created,
            model=model_name,
            choices=[{
                "index": 0,
                "delta": {},
                "finish_reason": "stop",
            }],
        )
        yield f"data: {final_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        error_chunk = ChatCompletionChunk(
            id=request_id,
            created=created,
            model=model_name,
            choices=[{
                "index": 0,
                "delta": {"content": f"\n\n[Error: {str(e)}]"},
                "finish_reason": "error",
            }],
        )
        yield f"data: {error_chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/chat/completions", response_model=None)
async def chat_completions(
    request: ChatCompletionRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key),
):
    """
    OpenAI-compatible chat completions endpoint.

    Supports both streaming and non-streaming modes.
    Compatible with Open WebUI and other OpenAI-compatible clients.
    """
    try:
        # Generate unique request ID
        request_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        created = int(time.time())
        model_name = request.model or "investigations-swine"

        # Извлечение пользовательского ввода и истории чата
        user_input = extract_user_input(request.messages)
        chat_history = extract_chat_history(request.messages)

        if not user_input:
            raise HTTPException(status_code=400, detail="No user message found in request")

        # Проверка, является ли это служебным запросом от Open WebUI (генерация заголовка и т.д.)
        is_service_request = any([
            "Generate a concise" in user_input and "title" in user_input.lower(),
            user_input.strip().startswith("### Task:"),  # Проверяем что сообщение начинается с "### Task:"
            "### Task:" in user_input and "### Guidelines:" in user_input,
            "JSON format:" in user_input and '"title"' in user_input,
        ])

        if is_service_request:
            logger.info(f"🔔 Service request detected: {user_input[:80]}...")

        # Определение investigation_id (автоматическое создание для первого сообщения)
        investigation_id = request.investigation_id
        is_new_investigation = False

        # Логирование для отладки
        logger.info(f"📨 Received {len(request.messages)} messages in request")
        for i, msg in enumerate(request.messages):
            preview = msg.content[:100] if msg.content else ""
            logger.info(f"  Message {i}: role={msg.role}, preview={preview}...")

        if not investigation_id:
            # Попытка извлечь из истории
            investigation_id = extract_investigation_id_from_history(request.messages)
            if investigation_id:
                logger.info(f"✅ Extracted investigation_id from history: {investigation_id}")
            else:
                logger.warning(f"⚠️ Could not extract investigation_id from {len(request.messages)} messages")

        # Создание нового investigation_id только для не-служебных запросов
        if not investigation_id and not is_service_request:
            # Первое сообщение - создаём новое расследование
            investigation_id = generate_investigation_id()
            is_new_investigation = True
            logger.info(f"Creating new investigation: {investigation_id}")
        elif is_service_request:
            # Служебный запрос без investigation_id - используем placeholder
            investigation_id = "service_request"
            logger.info(f"Service request detected, using placeholder investigation_id")

        logger.info(f"Chat request: {request_id}, investigation_id={investigation_id}, new={is_new_investigation}")
        logger.info(f"User input: {user_input[:100]}...")

        # Получение глобальных MCP клиента и менеджера расследований
        mcp_client: VetRetroMCPClient = http_request.app.state.mcp_client
        investigation_manager: InvestigationManager = http_request.app.state.investigation_manager

        # Определение типа животных на основе имени модели
        # модель "investigations-swine" -> свиньи (по умолчанию)
        # модель "investigations-poultry" -> птица
        animal_type = "pig"  # по умолчанию
        if model_name and "poultry" in model_name.lower():
            animal_type = "poultry"
            logger.info(f"Using poultry agent (animal_type={animal_type})")
        else:
            logger.info(f"Using swine agent (animal_type={animal_type})")

        # Создание папки расследования если новое (но не для служебных запросов)
        if is_new_investigation and not is_service_request:
            await investigation_manager.create_investigation_folder(investigation_id)
            logger.info(f"Created investigation folder: {investigation_id}")

        # Log LLM configuration before creating agent
        logger.info(f"🤖 Creating agent with model: {settings.LLM_MODEL}")
        logger.info(f"🔗 LLM API Base: {settings.LLM_API_BASE}")

        # Создание executor агента (с соответствующим типом животных)
        agent_executor = create_investigation_agent(
            investigation_id=investigation_id,
            mcp_client=mcp_client,
            investigation_manager=investigation_manager,
            animal_type=animal_type,
            max_iterations=50,  # Increased for complex veterinary investigations
        )

        # Оборачиваем файловые инструменты для автоматической инжекции investigation_id
        from functools import wraps
        FILE_TOOL_NAMES = ["write_file", "read_file", "list_files", "append_to_file", "update_file_section"]

        for tool in agent_executor.tools:
            if tool.name in FILE_TOOL_NAMES:
                original_run = tool._run

                @wraps(original_run)
                def make_wrapped_run(orig_fn, inv_id):
                    def wrapped_run(*args, **kwargs):
                        if 'investigation_id' not in kwargs or not kwargs.get('investigation_id'):
                            kwargs['investigation_id'] = inv_id
                            logger.debug(f"🔧 Wrapper injected investigation_id={inv_id} into {tool.name}")
                        return orig_fn(*args, **kwargs)
                    return wrapped_run

                tool._run = make_wrapped_run(original_run, investigation_id)

        # STREAMING MODE
        if request.stream:
            # Get the model that will be used by the agent from the LLM factory
            # This ensures we use the model from the provider mapping
            llm_factory = LLMClientFactory(settings)
            actual_model_name = llm_factory.get_model_for_agent()
            logger.info(f"STREAMING: Actual model that will be used: {actual_model_name}")

            return StreamingResponse(
                stream_agent_response(
                    agent_executor=agent_executor,
                    user_input=user_input,
                    chat_history=chat_history,
                    request_id=request_id,
                    model_name=model_name,
                    created=created,
                    investigation_id=investigation_id,
                    actual_model_used=actual_model_name,
                    is_new_investigation=is_new_investigation,
                    is_service_request=is_service_request,
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # Disable nginx buffering
                },
            )

        # NON-STREAMING MODE
        # Get the model that will be used by the agent from the LLM factory
        # This ensures we use the model from the provider mapping
        llm_factory = LLMClientFactory(settings)
        actual_model_name = llm_factory.get_model_for_agent()
        logger.info(f"NON-STREAMING: Actual model that will be used: {actual_model_name}")

        agent_input = {"input": user_input}
        if chat_history:
            agent_input["chat_history"] = chat_history

        result = await agent_executor.ainvoke(agent_input)

        # Extract output
        output_text = result.get("output", "")

        # Build response
        response = ChatCompletionResponse(
            id=request_id,
            created=created,
            model=model_name,  # Keep the original model name for the API response
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=output_text,
                    ),
                    finish_reason="stop",
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=0,  # TODO: calculate actual tokens
                completion_tokens=0,
                total_tokens=0,
            ),
        )

        return response

    except Exception as e:
        logger.error(f"Chat completion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models(api_key: str = Depends(verify_api_key)):
    """
    OpenAI-compatible models endpoint.

    Returns available models for compatibility with OpenAI clients.

    Two models are available:
    - investigations-swine: AI assistant for pig farming veterinary investigations
    - investigations-poultry: AI assistant for poultry farming veterinary investigations
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "investigations-swine",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "vetretro",
                "permission": [],
                "root": "investigations-swine",
                "parent": None,
            },
            {
                "id": "investigations-poultry",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "vetretro",
                "permission": [],
                "root": "investigations-poultry",
                "parent": None,
            },
        ],
    }
