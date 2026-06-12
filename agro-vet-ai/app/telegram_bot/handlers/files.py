import os

from app.utils.abbreviations import expand_abbreviations
from app.utils.logger import get_logger
from app.utils.parsers.converter_factory import ConverterFactory
from config.config import Config

app_logger = get_logger(__name__)

cfg = Config.from_yaml()


async def handle_file(message):
    # Создаем папки для сохранения файла
    os.makedirs("tmp", exist_ok=True)  # exist_ok=True предотвращает ошибку, если папка уже есть

    # Если загружен файл, читаем его содержимое
    if message.document:
        file_size = message.document.file_size
        file_id = message.document.file_id

    else:
        # Загруженные фотографии всегда представлены в виде списка.
        photo = message.photo[0]
        file_size = photo.file_size
        file_id = photo.file_id

    if file_size > cfg.max_file_size_mb * 1024 * 1024:
        return await message.answer(f"Загрузите файл меньшего размера (<20 Mb).",  parse_mode="HTML")

    # Получить расширение файла
    file_info = await message.bot.get_file(file_id)
    file_path = file_info.file_path
    # Получить расширение из file_path (содержит точку, например, ".jpg")
    full_extension = os.path.splitext(file_path)[-1]
    file_extension = full_extension[1:]  # Получить расширение без точки

    # Сохранить файл по указанному пути

    local_path = f"tmp/{file_info.file_unique_id}.{file_extension}"

    await message.bot.download_file(file_info.file_path, local_path)

    # Обработка файлов в зависимости от их типа
    file_data = ConverterFactory(local_path).convert()

    # Проверяет, является ли file_data None
    if not file_data:
        # Удаляем файл при ошибке
        try:
            if os.path.exists(local_path):
                os.remove(local_path)
        except OSError as e:
            app_logger.error(f"Ошибка при удалении временного файла: {e}")
        return await message.answer("Произошла ошибка. Попробуйте загрузить другой файл.",  parse_mode="HTML")

    # Заменяем сокращения на полные названия
    user_message = expand_abbreviations(message.caption) if message.caption else ""
    # Объединяем сообщение пользователя и текст из файла для классификации
    user_message = f"{user_message}\n{file_data}".strip()

    # Возвращаем кортеж: (текст для классификации, путь к файлу для специализированной обработки)
    return user_message, local_path
