# import os
import asyncio
import time
import traceback
from aiogram import Bot, Dispatcher
# from dotenv import load_dotenv
from funcs.handlers import router

TG_TOKEN='6824090784:AAFB8JAp48dhAtCHKmPh8zzFcUV_24XVNPg'

async def tg_polling():
    # load_dotenv()
    # bot = Bot(token=os.getenv('TG_TOKEN'))
    bot = Bot(token=TG_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    try:
        await dp.start_polling(bot)
    except:
        traceback_error_string=traceback.format_exc()
        with open("/app/log/tg_errors.log", "a") as myfile:
            myfile.write("\r\n\r\n" + time.strftime("%c")+"\r\n<<ERROR polling>>\r\n"+ traceback_error_string + "\r\n<<ERROR polling>>")
        await dp.stop_polling(bot)
        time.sleep(10)
        await tg_polling()

if __name__ == '__main__':
    asyncio.run(tg_polling())
