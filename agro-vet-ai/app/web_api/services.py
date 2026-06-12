import os
import uuid
from typing import List
from fastapi import UploadFile

from app.agents.router.agent import TopicRouterAgent
from app.agents.router.models import TopicRouterAgentResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
from app.utils.abbreviations import expand_abbreviations
from app.utils.parsers.converter_factory import ConverterFactory


# Максимально допустимый размер загружаемого файла в мегабайтах
MAX_FILE_SIZE_MB = 20


async def handle_request(
        message: str | None,
        file: UploadFile | None,
        dialog_history: list[dict[str, str]] = None,
        file_path_override: str | None = None
) -> TopicRouterAgentResponse:
    """
    Обрабатывает сообщение и/или файл, выполняет преобразование и вызывает TopicRouter.

    :param message: Сообщение пользователя.
    :param dialog_history: История диалога.
    :param file: Загружаемый файл.
    :param file_path_override: Необязательный путь к файлу для использования вместо обработки загрузки файла
    :return: Ответ GPT.
    """
    logger.info(f"🌐 [handle_request] Начинаем обработку запроса")
    logger.info(f"💬 Сообщение: {message[:50] if message else 'None'}...")

    file_data = ""
    file_path = file_path_override  # Используем замену, если она предоставлена

    # Создаём временную директорию для хранения файлов, если она не существуют
    os.makedirs("tmp", exist_ok=True)
    if file and not file_path_override:  # Обрабатываем загрузку файла только если file_path_override не предоставлен
        try:
            # Логируем метаданные файла
            file_metadata = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": None  # Определим ниже
            }

            # Определяем размер файла
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)
            file_metadata["size"] = file_size

            logger.info(f"📁 [Web API] Метаданные файла: {file_metadata}")

            if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                logger.warning(
                    f"⚠️ [Web API] Файл слишком большой: {file_size} байт")
                return TopicRouterAgentResponse(response="Загрузите файл меньшего размера (<20 Mb).")

            # Генерация уникального имени файла с сохранением расширения
            file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
            file_path = f"tmp/{uuid.uuid4()}.{file_ext}"
            logger.info(f"📎 [Web API] Сохраняем файл как: {file_path}")

            # Сохраняем файл на диск
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            # Обработка файлов в зависимости от их типа
            file_data = ConverterFactory(file_path).convert()
            if not file_data:
                logger.warning(
                    "⚠️ [Web API] Файл пустой либо не удалось прочитать его содержимое.")
                return TopicRouterAgentResponse(response="Файл пустой либо не удалось прочитать его содержимое.")

            logger.info(f"📝 [Web API] Успешно извлечен текст из файла, длина: {len(file_data)} символов")

        except Exception as e:
            logger.error(
                f"💥 Ошибка при обработке файла: {str(e)}",
                exc_info=True
            )
            return TopicRouterAgentResponse(response="Ошибка при обработке файла.")
    elif file_path_override:
        # Если предоставлен file_path_override, извлекаем текст из указанного файла
        try:
            # Обработка файлов в зависимости от их типа
            file_data = ConverterFactory(file_path_override).convert()
            if not file_data:
                logger.warning(
                    f"⚠️ [Web API] Файл по пути {file_path_override} пустой либо не удалось прочитать его содержимое.")
                return TopicRouterAgentResponse(response="Файл пустой либо не удалось прочитать его содержимое.")

            logger.info(f"📝 [Web API] Успешно извлечен текст из файла {file_path_override}, длина: {len(file_data)} символов")

        except Exception as e:
            logger.error(
                f"💥 Ошибка при обработке файла {file_path_override}: {str(e)}",
                exc_info=True
            )
            return TopicRouterAgentResponse(response="Ошибка при обработке файла.")

    # Заменяем сокращения на полные названия
    user_message = expand_abbreviations(message or "")
    if file_data:
        user_message = f"{user_message}\n{file_data}".strip()

    logger.info(
        f"📝 Финальное сообщение для обработки: {user_message[:100]}...")

    # Используем агент напрямую вместо TopicRouter
    logger.info("🚀 Вызываем agent-based router напрямую")
    try:
        # Получаем экземпляр агент-роутера
        agent_router = TopicRouterAgent(dialog_history=dialog_history)
        result = agent_router.process(question=user_message, file_path=file_path, user_id=None)
        logger.info(f"✅ Получен ответ от agent-based router,\n{result.response[:100]}...")
        return result
    except Exception as e:
        logger.error(f"💥 Ошибка при обработке через agent-based router: {str(e)}", exc_info=True)
        response_text = "Произошла ошибка при обработке запроса. Пожалуйста, повторите попытку."
        return TopicRouterAgentResponse(response=response_text)
