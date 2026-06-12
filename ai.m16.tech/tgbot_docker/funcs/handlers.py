# import os
from aiogram import F, Router, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import requests
# from dotenv import load_dotenv

# load_dotenv()
# PRICE_ID = os.getenv('PRICE_ID')
# REGLAMENT_ID = os.getenv('REGLAMENT_ID')
PRICE_ID='12Fj1RcAr0yB6PLtq_S6MH27I0wVV0Fgo8_QkACrovvo'
REGLAMENT_ID='L32jhOaPfgOwIRSj5FPy1JxCQ22T1cBlR6IStDGhDGE'

router = Router()

@router.message(CommandStart())
async def send_welcome(message: Message):
    #await message.answer('Привет!', reply_markup=kb.main)
    await message.answer("Добрый день! Я цифровой помощник ЦОП, чем я могу вам помочь?")


# @router.message(Command('help'))
# async def cmd_help(message: Message):
#     await message.answer('Вы нажали на кнопку помощи')


@router.message(Command('reset'))
async def clear_history(message: Message):
    try:
        requests.post('http://app:5000/api/chat_helper_clear',
                            json={
                                "from_id": message.from_user.id
                                },
                            auth=requests.auth.HTTPBasicAuth('user', '{{API_PASSWORD}}'),
                            timeout=30
                            )
    except Exception as e:
        message.answer(message.from_user.id, f"Произошла ошибка, попробуйте позже! {e}")
        return
    await message.answer('История чата очищена!')

@router.message()
async def generate_reply_message(message: Message):
    # await router.send_chat_action(chat_id=message.from_user.id, action=types.ChatAction.TYPING)
    try:
        #result = requests.post('http://app:5000/api/chat_helper',
        result = requests.post('http://app:5000/api/chat_helper',
                            json={
                                "user_promt": message.text,
                                "table_id": PRICE_ID,
                                "text_id": REGLAMENT_ID,
                                "from_id": message.from_user.id
                                },
                            auth=requests.auth.HTTPBasicAuth('user', '{{API_PASSWORD}}'),
                            timeout=30
                            )
        result = list(result.json().values())
        await message.answer(result[0])
        await message.answer(result[1])
    except Exception as e:
        await message.answer(f"Произошла ошибка, попробуйте позже! {e}")
    # await router.send_chat_action(chat_id=message.from_user.id, action=types.ChatAction.STOP_TYPING)
