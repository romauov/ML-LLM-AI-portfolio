"""
скрипт для запуска ботов

@author Sergei Romanov
"""
import asyncio
import traceback
from aiogram import Bot, Dispatcher
from functools import partial

from clients.meatinfo.handlers import meatinfo_router
from clients.edelweis.handlers import edelweis_router
from clients.shaurmatika.handlers import shaurmatika_router
from clients.selezneva.handlers import selezneva_router
from clients.torgkit.handlers import torgkit_router
from clients.nomadic_essen.handlers import nomadic_essen_router
from clients.muksun.handlers import muksun_router
from utils.middleware import UserThrottlingMiddleware
from utils.settings import secrets as s
from utils.traceback_error_log import log_traceback


def create_bots_and_dispatchers(tokens_and_routers):
    """инициализация ботов и диспетчеров

    Args:
        tokens_and_routers (List): список кортежей (токен, роутер)

    Returns:
        List: список кортежей (бот, диспетчер)
    """
    bots_and_dispatchers = []
    for token, router in tokens_and_routers:
        bot = Bot(token=token)
        dispatcher = Dispatcher()
        dispatcher.message.middleware(UserThrottlingMiddleware(limit=2.0))
        dispatcher.include_router(router=router)
        bots_and_dispatchers.append((bot, dispatcher))
    return bots_and_dispatchers


async def start_polling(dispatcher, bot):
    """функция запуска отдельного бота

    Args:
        dispatcher (Dispatcher): aiogram dicspatcher object
        bot (Bot): aiogram bot object
    """
    await dispatcher.start_polling(bot)


async def tg_polling(tokens_and_routers):
    """запуск всех ботов

    Args:
        tokens_and_routers (List): список кортежей (токен, роутер)
    """
    try:
        bots_and_dps = create_bots_and_dispatchers(tokens_and_routers)
        tasks = [partial(start_polling, dispatcher, bot)() for bot, dispatcher in bots_and_dps]
        await asyncio.gather(*tasks)

    except Exception as err:
        traceback_error_string=traceback.format_exc()
        log_traceback(traceback_error_string=traceback_error_string, error=err) 
        await asyncio.sleep(600)
        await tg_polling(tokens_and_routers)

if __name__ == '__main__':
    tokens_and_routers = [
        (s.meatinfo.token, meatinfo_router),
        (s.edelweis.token, edelweis_router),
        (s.shaurmatika.token, shaurmatika_router),
        # (s.selezneva.token, selezneva_router),
        # (s.torgkit.token, torgkit_router),
        (s.nomadic_essen.token, nomadic_essen_router),
        (s.muksun.token, muksun_router)
        ]
    asyncio.run(tg_polling(tokens_and_routers))
