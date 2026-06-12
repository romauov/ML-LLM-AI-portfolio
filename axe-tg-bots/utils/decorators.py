"""
декораторы для повторной генерации при ошибке и для переслыки сообщений в тг-канал

@author Sergei Romanov
"""
import asyncio
import random
from functools import wraps

import openai


def exponential_backoff(
    max_retries=5,
    base_delay=1,
    max_delay=60
):
    """Декоратор с экспоненциальной задержкой и обработкой специфичной ошибки 403

    Args:
        max_retries (int): Максимальное количество попыток для временных ошибок
        base_delay (int): Базовая задержка в секундах
        max_delay (int): Максимальная задержка в секундах
        on_403_callback (coroutine): Колбэк для отправки уведомления об ошибке 403
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)

                except (openai.RateLimitError, openai.InternalServerError, openai.APIConnectionError) as e:
                    retries += 1
                    if retries > max_retries:
                        raise

                    delay = min(base_delay * (2 ** retries) +
                                random.uniform(0, 1), max_delay)

                    await asyncio.sleep(delay)

                except Exception as e:
                    # Обработка специфической ошибки 403
                    if (
                        hasattr(e, 'status_code')
                        and e.status_code == 403
                        and 'unsupported_country_region_territory' in str(e)
                    ):
                        # Ждем ровно 2 часа (7200 секунд)
                        await asyncio.sleep(7200)

                        # Повторяем попытку только один раз после ожидания
                        try:
                            return await func(*args, **kwargs)
                        except Exception as e:
                            raise RuntimeError("Retry after 403 failed") from e

                    else:
                        raise
        return wrapper
    return decorator
