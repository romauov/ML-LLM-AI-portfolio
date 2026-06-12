"""
скрипт для запуска ботов

@author Sergei Romanov
"""
import asyncio
from aiogram import Bot, Dispatcher


from conversator.handlers import meatinfo_router
from utils.settings import secrets as s



async def main():
    
    bot = Bot(token=s.meatinfo.token)
    dp = Dispatcher()
    dp.include_router(meatinfo_router)
    
    await dp.start_polling(bot)
    
    
if __name__ == "__main__":
    asyncio.run(main())