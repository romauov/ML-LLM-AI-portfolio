import json
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Body, Depends
from fastapi.responses import JSONResponse

from app.agents.router.agent import TopicRouterAgent
from app.agents.router.models import TopicRouterAgentResponse
from app.utils.abbreviations import expand_abbreviations
from app.web_api.models import DialogHistory, SubmitRequest
from app.web_api.services import handle_request
from app.utils.logger import get_logger

logger = get_logger(__name__)
from app.web_api.auth import verify_api_key


router = APIRouter()


@router.get("/api/up", status_code=200)
async def up(api_key: str = Depends(verify_api_key)):
    """
    Проверка работоспособности API-сервера.

    Возвращает статус 200, если сервер доступен.
    """
    return "API up"


@router.post("/api/submit", response_class=JSONResponse)
async def submit(
        message: str = Form(None),
        file_contents: UploadFile = File(None),
        dialog_history: DialogHistory = Form(None),
        api_key: str = Depends(verify_api_key)
):
    """
    Обрабатывает пользовательский запрос или загружаемый файл.

    :param message: Текст сообщения пользователя.
    :param dialog_history: История диалога.
    :param file_contents: Содержимое файла.
    :param api_key: API key for authentication.
    :return: Результат обработки или сообщение об ошибке.
    """
    if message is None and file_contents is None:
        raise HTTPException(
            status_code=400, detail="Нужно передать хотя бы сообщение или файл.")

    if dialog_history:
        dialog_history = json.loads(
            dialog_history.model_dump_json()).get('dialog')

    try:
        result: TopicRouterAgentResponse = await handle_request(
            message=message,
            file=file_contents,
            dialog_history=dialog_history,
            file_path_override=None  # файл обрабатывается через file параметр
        )
        return result.model_dump()
    except Exception as e:
        logger.error(
            "Error in submit()",
            exc_info=True,
            extra={
                "user_message": message,
                "filename": file_contents.filename if file_contents else None,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=500, detail="Ошибка при обработке запроса пользователя.")


@router.post("/api/submit_json", response_class=JSONResponse)
async def submit_json(payload: SubmitRequest, api_key: str = Depends(verify_api_key)):
    """
    JSON-версия эндпоинта для promptfoo тестов.

    ОТЛИЧИЯ ОТ /api/submit:
    - НЕ использует dialog_history (игнорируется)
    - НЕ поддерживает файлы
    - Возвращает результат в формате {"response": str, "context": str}

    Ожидает:
    {
        "message": str,
        "dialog_history": [...],  # ИГНОРИРУЕТСЯ
    }
    """
    try:
        logger.info(f"🚀 [submit_json] Обрабатываем запрос БЕЗ dialog_history")

        # Заменяем сокращения
        user_message = expand_abbreviations(payload.message or "")

        # Вызываем агент напрямую
        agent_router = TopicRouterAgent()
        result = agent_router.process(question=user_message)

        logger.info(f"[submit_json] Ответ получен, response: {len(result.response)} символов, "
                    f"context: {len(result.context)} символов, "
                    f"context_images: количество изображений {len(result.context_images)}")
        return result.model_dump()

    except Exception as e:
        logger.error(
            "Error in submit_json()",
            exc_info=True,
            extra={
                "user_message": payload.message if payload else None,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=500, detail="Ошибка при обработке запроса пользователя.")
