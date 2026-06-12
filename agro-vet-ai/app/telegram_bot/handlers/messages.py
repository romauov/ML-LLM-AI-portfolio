import asyncio
import base64
import os
import re
import traceback

from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, BufferedInputFile, InputMediaPhoto

from app.utils.abbreviations import expand_abbreviations
from app.agents.router.agent import TopicRouterAgent
from app.telegram_bot.constants import RESET_DIALOG, ERROR_TRY_RESET_ANSWER, RESET_DIALOG_ANSWER, SORRY_ERROR_ANSWER
from app.telegram_bot.handlers.files import handle_file
from app.telegram_bot.handlers.keyboard import create_standard_keyboard
from app.telegram_bot.handlers.loadings import create_wait_response_task, cancel_wait_response_task
from app.telegram_bot.handlers.text_cleaner import balance_html_tags, clean_text
from app.utils.dialog_history import get_user_dialog_history, save_user_dialog
from app.utils.logger import get_logger

app_logger = get_logger(__name__)


router = Router()


async def send_message(message: Message, text: str, images: list[str] = None, reply_markup: ReplyKeyboardMarkup = None):
    """
    Функция отправки сообщения. Если текст превышает лимит символов, 
    то выполняется отправка по частям с независимой балансировкой тегов для каждой части.
    """
    MAX_LENGTH = 4096
    
    try:
        # Очищаем текст без балансировки
        cleaned_text = clean_text(text)
    except Exception as e:
        app_logger.error(f"Ошибка очистки текста: {e}")
        cleaned_text = text
    
    # Если текст короткий - балансируем и отправляем целиком
    if len(cleaned_text) <= MAX_LENGTH:
        try:
            balanced_text = balance_html_tags(cleaned_text)
            await message.answer(balanced_text, reply_markup=reply_markup, parse_mode='HTML')
        except Exception as e:
            app_logger.error(f"Ошибка отправки сообщения: {e}")
            # Фолбэк: отправляем без HTML
            plain_text = re.sub(r'<[^>]+>', '', cleaned_text)
            await message.answer(plain_text[:MAX_LENGTH], reply_markup=reply_markup)
    else:
        # Разбиваем текст на части
        parts = []
        current_part = ""

        # Разбиваем по абзацам для сохранения логической структуры
        paragraphs = cleaned_text.split('\n')

        for paragraph in paragraphs:
            # Если добавление нового абзаца не превышает лимит
            if len(current_part) + len(paragraph) + 1 <= MAX_LENGTH:
                current_part += "\n" + paragraph if current_part else paragraph
            else:
                # Если текущая часть не пуста - сохраняем её
                if current_part:
                    parts.append(current_part)
                    current_part = ""

                # Если один абзац слишком длинный - разбиваем по словам
                if len(paragraph) > MAX_LENGTH:
                    words = paragraph.split(' ')
                    for word in words:
                        if len(current_part) + len(word) + 1 > MAX_LENGTH:
                            if current_part:
                                parts.append(current_part)
                                current_part = word
                            else:
                                # Одно слово слишком длинное - разбиваем по символам
                                parts.append(word[:MAX_LENGTH])
                                current_part = word[MAX_LENGTH:]
                        else:
                            current_part += " " + word if current_part else word
                else:
                    current_part = paragraph

        # Добавляем последнюю часть
        if current_part:
            parts.append(current_part)

        # Отправляем части с независимой балансировкой тегов для каждой части
        for i, part in enumerate(parts):
            current_reply_markup = reply_markup if i == len(parts) - 1 else None

            if part.strip():
                try:
                    # Балансируем теги для каждой части независимо
                    balanced_part = balance_html_tags(part)
                    await message.answer(balanced_part, reply_markup=current_reply_markup, parse_mode='HTML')
                except Exception as e:
                    app_logger.error(f"Ошибка отправки части сообщения: {e}")
                    # Фолбэк для части
                    plain_part = re.sub(r'<[^>]+>', '', part)
                    await message.answer(plain_part[:MAX_LENGTH], reply_markup=current_reply_markup)

                await asyncio.sleep(0.3)  # Небольшая задержка между сообщениями

    if images:
        tg_photos = []
        for i, image in enumerate(images):
            buffered_image = BufferedInputFile(
                file=base64.b64decode(image.encode()),
                filename=f'{i}.png'
            )
            tg_photos.append(InputMediaPhoto(media=buffered_image))

        # отправляем батчами по 10
        for i in range(0, len(tg_photos), 10):
            chunk = tg_photos[i:i + 10]
            await message.answer_media_group(media=chunk, allow_sending_without_reply=True)


@router.message()
async def message_handler(message: Message) -> None:
    """Обрабатываем текстовые сообщения и загруженные файлы."""
    file_path = None
    try:
        user_id = message.from_user.id
        dialog_history = await get_user_dialog_history(user_id, RESET_DIALOG_ANSWER)

        if message.document or message.photo:
            file_result = await handle_file(message)
            if isinstance(file_result, Message):
                return
            user_message, file_path = file_result
        else:
            user_message = expand_abbreviations(message.text)

        await save_user_dialog(user_id, "user", user_message)
        loading_tasks = await create_wait_response_task(message)

        images = None
        file_requests = None
        if user_message == RESET_DIALOG:
            response = RESET_DIALOG_ANSWER
            response_role = "assistant"
        else:
            try:
                agent_router = TopicRouterAgent(dialog_history=dialog_history, user_id=user_id)
                result = agent_router.process(user_message, file_path=file_path, user_id=user_id)
                response = result.response
                images = result.context_images
                file_requests = result.file_requests
                response_role = "assistant"
            except Exception as e:
                app_logger.error(f"Ошибка при обработке через agent-based router: {e}")
                response = SORRY_ERROR_ANSWER
                response_role = "assistant"

        reply_keyboard = create_standard_keyboard()
        await cancel_wait_response_task(loading_tasks)
        await send_message(message, response, images=images, reply_markup=reply_keyboard)
        await save_user_dialog(user_id, response_role, response)

        # Отправляем файлы с инструкциями, если они были запрошены
        if file_requests:
            for file_request in file_requests:
                trade_name = file_request.get('trade_name', 'instruction')
                file_content = file_request.get('file_content', '')
                file_extension = file_request.get('file_extension', '.txt')

                if file_content:
                    # Создаем файл в памяти
                    file_bytes = file_content.encode('utf-8')
                    buffered_file = BufferedInputFile(
                        file=file_bytes,
                        filename=f"{trade_name}{file_extension}"
                    )
                    await message.answer_document(document=buffered_file)
                    app_logger.info(f"Отправлен файл инструкции: {trade_name}{file_extension}")

    except Exception:
        error_message = traceback.format_exc()
        app_logger.error(f"Ошибка при обработке сообщения: {error_message}")
        await message.answer(ERROR_TRY_RESET_ANSWER, parse_mode='HTML')
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                app_logger.info(f"Удален временный файл: {file_path}")
            except OSError as e:
                app_logger.error(f"Ошибка при удалении временного файла {file_path}: {e}")
