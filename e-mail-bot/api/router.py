"""
роутер FastAPI

@author Sergei Romanov
"""
import json
from fastapi import APIRouter, HTTPException
from api.logger import logger as log
from api.schemas import UserRequest, UserResponse, GptTemplaterRequest, GptTemplaterResponse
from gpt.response_generation_gpt import generate_qr_gpt
from gpt.templater import generate_openai_response

router = APIRouter()


@router.post("/get_qr/")
async def generate_response(request: UserRequest) -> UserResponse:
    """POST запрос к API для получения быстрого ответа"""
    try:
        log.info(json.dumps({
            "request": request.model_dump(),
            "type": "request"
        }, ensure_ascii=False))

        response_message = await generate_qr_gpt(request)

        if not response_message:
            raise HTTPException(status_code=404, detail="Users not found")

        response = UserResponse(quick_reply=response_message)

        log.info(json.dumps({
            "response": response.model_dump(),
            "type": "response"
        }, ensure_ascii=False))

        return response

    except HTTPException as http_error:
        log.error(json.dumps({
            "error": {
                "status_code": http_error.status_code,
                "detail": http_error.detail
            },
            "type": "error"
        }, ensure_ascii=False))
        raise http_error

    except Exception as e:
        log.error(json.dumps({
            "error": {
                "type": str(type(e).name),
                "message": str(e)
            },
            "type": "error"
        }, ensure_ascii=False))
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/gpt_templater_v2", response_model=GptTemplaterResponse)
async def generate_v2(request: GptTemplaterRequest):
    """
    API доступно по url: https://ai.m16.tech/api/gpt_templater_v2
    
    Принимает POST запрос с данными в формате GptTemplaterRequest
    
    Возвращает: {
        "title": "Заголовок",
        "text": "Текст сгенерированного коммерческого предложения"
    }
    """
    try:
        log.info(json.dumps({
            "request": request.model_dump(),
            "type": "request"
        }, ensure_ascii=False))

        result = await generate_openai_response(request)


        log.info(json.dumps({
            "response": result.model_dump(),
            "type": "response"
        }, ensure_ascii=False))

        return result

    except HTTPException as http_error:
        log.error(json.dumps({
            "error": {
                "status_code": http_error.status_code,
                "detail": http_error.detail
            },
            "type": "error"
        }, ensure_ascii=False))
        raise http_error

    except Exception as e:
        log.error(json.dumps({
            "error": {
                "type": str(type(e).name),
                "message": str(e)
            },
            "type": "error"
        }, ensure_ascii=False))
        raise HTTPException(status_code=500, detail="Internal Server Error")    
