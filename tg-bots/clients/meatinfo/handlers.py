"""
обработчик сообщений aiogram

@author Sergei Romanov
"""
import traceback
from aiogram import Bot, Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ChatAction
from aiogram.utils.chat_action import ChatActionSender
from clients.meatinfo.conversator import MeatinfConversator
from clients.meatinfo.keyboards import example_buttons
from utils.aiogram_keyboards import extended_kb, model_kb
from utils.decorators import forward_and_send_message
from utils.settings import secrets as s
from utils.traceback_error_log import report_error


class ModelUpdate(StatesGroup):
    model = State()


meatinfo_conversator = MeatinfConversator(
    table_id=s.meatinfo.price_id,
    text_id=s.meatinfo.reglament,
    name='meatinfo',
    model='gpt-4o-mini')

meatinfo_router = Router()


@meatinfo_router.message(CommandStart())
async def send_welcome(message: Message):
    """обработка команды старт

    Args:
        message (Message): telegram message object
    """
    await message.answer(
        "Привет! Я Цифровой Ассистент Отдела продаж. Моя задача - оперативно ответить на вопросы ваших клиентов и собрать для вас необходимую информацию о них. Можете попробывать позадавать мне вопросы о моей деятельности и я покажу, как я могу отвечать. После наймите меня в свою команду, я буду отличным помощником!",
        reply_markup=await extended_kb(example_buttons))


@meatinfo_router.message(Command('update'))
async def update_instructions(message: Message):
    """ обработка команды для обновления промта

    Args:
        message (Message): telegram message object
    """
    meatinfo_conversator.update()
    await message.answer('Инструкции обновлены.')


@meatinfo_router.message(Command('model'))
async def change_model(message: Message, state: FSMContext):
    if message.from_user.id not in s.meatinfo.admin_ids:
        await message.reply(f"У вас нет прав для выполнения этой команды.")
        return
    await state.set_state(ModelUpdate.model)
    await message.answer("Выберите модель из списка", reply_markup=await model_kb())


@meatinfo_router.message(ModelUpdate.model)
async def set_model(message: Message, state: FSMContext):
    # await state.update_data(model=message.text)
    # data = await state.get_data()
    meatinfo_conversator.change_model(message.text.split(' ', maxsplit=1)[0])
    await message.answer(f'Установлена модель {getattr(meatinfo_conversator, "model")}',
                         reply_markup=await extended_kb(example_buttons))
    await state.clear()


@meatinfo_router.message()
@forward_and_send_message(s.meatinfo.channel_id, s.meatinfo.manager_ids, meatinfo_conversator)
async def generate_reply_message(message: Message, bot: Bot):
    """обработка сообщения с помощью Chat GPT

    Args:
        message (Message): telegram message object
        bot (Bot): telegram bot object
    """
    # sender для долгого отображения typing...
    action_sender = ChatActionSender(
        bot=message.bot,
        chat_id=message.chat.id,
        action=ChatAction.TYPING
    )
    try:
        async with action_sender:
            result = await meatinfo_conversator.generate_reply(message)
            await message.answer(result['reply'],
                                 reply_markup=await extended_kb(example_buttons))
            return result

    except Exception as e:
        await report_error(
            message=message,
            bot=bot,
            bot_name=getattr(meatinfo_conversator, 'path')[5:],
            errors_channel_id=s.errors_channel_id,
            error=e,
            traceback_error_string=traceback.format_exc()
        )
