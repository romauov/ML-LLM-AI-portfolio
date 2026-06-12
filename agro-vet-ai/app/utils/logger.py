import logging
import os
from datetime import datetime


def get_logger(name: str):
    """Создает логгер с уровнем логирования в зависимости от режима"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        try:
            # Устанавливаем уровень логирования в зависимости от режима
            from app.utils.settings import secrets as s
            if s.mode in ['dev', 'debug']:
                logger.setLevel(logging.DEBUG)
            elif s.mode == 'prod':
                logger.setLevel(logging.INFO)
            else:
                logger.setLevel(logging.INFO)  # По умолчанию
        except:
            logger.setLevel(logging.INFO)  # По умолчанию

        # Создаем основную папку для логов
        today = datetime.now().strftime("%Y-%m-%d")
        main_dir = f"logs/{today}"
        os.makedirs(main_dir, exist_ok=True)

        # Форматтер
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Основной файл логов
        main_handler = logging.FileHandler(f"{main_dir}/app.log", encoding='utf-8')
        main_handler.setFormatter(formatter)
        main_handler.setLevel(logging.DEBUG)  # В файл всегда пишем все

        # Консольный вывод
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Уровень для консоли зависит от режима
        try:
            from app.utils.settings import secrets as s
            if s.mode in ['dev', 'debug']:
                console_handler.setLevel(logging.DEBUG)
            elif s.mode == 'prod':
                console_handler.setLevel(logging.INFO)
            else:
                console_handler.setLevel(logging.INFO)
        except:
            console_handler.setLevel(logging.INFO)

        # Обработчик ошибок в один файл
        error_handler = logging.FileHandler(f"{main_dir}/errors.log", encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        # Добавляем все обработчики
        logger.addHandler(main_handler)
        logger.addHandler(console_handler)
        logger.addHandler(error_handler)

    return logger
