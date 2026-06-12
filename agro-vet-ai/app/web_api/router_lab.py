import os
import tempfile
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.utils.abbreviations import expand_abbreviations
from app.topics.questions.lab_test_classifier.topic_handler import LabTestClassifier
from app.utils.logger import get_logger

logger = get_logger(__name__)
from app.web_api.auth import verify_api_key


router = APIRouter()


@router.post("/api/process_lab_results", response_class=JSONResponse)
async def process_lab_results(
    message: str = Form(None),
    lab_results: str = Form(None),  # Текстовая версия лабораторных результатов
    file_contents: UploadFile = File(None), # Файл с результатами лабораторных исследований
    api_key: str = Depends(verify_api_key)
):
    """
    Обрабатывает результаты лабораторных исследований.

    :param lab_results: Текстовая версия лабораторных результатов.
    :param file_contents: Файл с результатами лабораторных исследований (PDF, изображение и т.д.).
    :param api_key: API key for authentication.
    :return: Результат обработки лабораторных результатов или сообщение об ошибке.
    """
    # Проверяем, что пришли только lab_results или только файл, но не оба
    if lab_results is not None and file_contents is not None:
        raise HTTPException(
            status_code=400, detail="Нужно передать либо текстовую версию лабораторных результатов, либо файл с результатами, но не оба источника одновременно.")

    if lab_results is None and file_contents is None:
        raise HTTPException(
            status_code=400, detail="Нужно передать либо текстовую версию лабораторных результатов, либо файл с результатами.")

    # Если есть файл, сохраняем его и используем в обработке
    file_path = None
    if file_contents:

        # Создаем временный файл для загруженного содержимого
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f"_{file_contents.filename}",
            mode='wb'
        ) as temp_file:
            content = await file_contents.read()
            temp_file.write(content)
            file_path = temp_file.name

    try:

        # Подготовка контекста с лабораторными результатами
        context = {"lab_results": expand_abbreviations(lab_results)} if lab_results else None

        handler = LabTestClassifier()
        result = handler.process(
            question=message,
            context=context,
            file_path=file_path
        )

        # Преобразуем результат в нужный формат
        if isinstance(result, dict):
            return {"response": result.get("content", ""), "context": ""}
        else:
            return {"response": str(result), "context": ""}

    except Exception as e:
        logger.error(
            "Error in process_lab_results()",
            exc_info=True,
            extra={
                "user_message": message,
                "context": lab_results,
                "filename": file_contents.filename if file_contents else None,
                "error": str(e)
            }
        )
        # Удаляем временный файл при ошибке
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
        raise HTTPException(
            status_code=500, detail="Ошибка при обработке лабораторных результатов.")
    finally:
        # Удаляем временный файл, если он был создан
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
