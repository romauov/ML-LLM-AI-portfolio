"""
обработчик сообщений aiogram

@author Nikolay Zhabchikov
"""
import traceback
from aiogram import Router, Bot
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.chat_action import ChatActionSender
from aiogram.types import Message
from clients.nomadic_essen.conversation_nommadic_essen import ConversatorNomadicEssen
from clients.nomadic_essen.keyboards import example_buttons
from utils.traceback_error_log import report_error
from utils.aiogram_keyboards import extended_kb, model_kb
from utils.decorators import forward_and_send_message
from utils.settings import secrets as s


class ModelUpdate(StatesGroup):
    model = State()


nomadic_essen_conversator = ConversatorNomadicEssen(
    table_id=None,
    text_id=s.nomadic_essen.reglament,
    name='nomadic_essen',
    model='gpt-4o-mini'
)

nomadic_essen_router = Router()


@nomadic_essen_router.message(CommandStart())
async def send_welcome(message: Message):
    """обработка команды старт

    Args:
        message (Message): telegram message object
    """
    text = 'Здравствуйте! Я готов ответить на вопросы. Что вас интересует?'
    await message.answer(text, reply_markup=await extended_kb(example_buttons))


@nomadic_essen_router.message(Command('update'))
async def update_instructions(message: Message):
    """ обработка команды для обновления промта

    Args:
        message (Message): telegram message object
    """
    nomadic_essen_conversator.update()
    await message.answer('Инструкции обновлены.')


@nomadic_essen_router.message(Command('model'))
async def change_model(message: Message, state: FSMContext):
    """обработка команды выбора Chat GPT модели

    Args:
        message (Message): telegram message object
        state (FSMContext): telegram context object
    """
    if message.from_user.id not in s.nomadic_essen.admin_ids:
        await message.reply("У вас нет прав для выполнения этой команды.")
        return

    await state.set_state(ModelUpdate.model)
    await message.answer("Выберите модель из списка", reply_markup=await model_kb())


@nomadic_essen_router.message(ModelUpdate.model)
async def set_model(message: Message, state: FSMContext):
    """обработка выбора Chat GPT модели с клавиатуры

    Args:
        message (Message): telegram message object
        state (FSMContext): telegram context object
    """
    nomadic_essen_conversator.change_model(message.text.split(' ', maxsplit=1)[0])

    text = f'Установлена модель {getattr(nomadic_essen_conversator, "model")}'
    await message.answer(text, reply_markup=await extended_kb(example_buttons))
    await state.clear()


@nomadic_essen_router.message()
@forward_and_send_message(s.nomadic_essen.channel_id, s.nomadic_essen.manager_ids, nomadic_essen_conversator)
async def generate_reply_message(message: Message, bot: Bot):
    """обработка сообщения с помощью Chat GPT

    Args:
        message (Message): telegram message object
        bot (Bot): telegram bot object
    """
    # sender для долгого отображения typing...
    action_sender = ChatActionSender(
        bot=bot,
        chat_id=message.chat.id,
        action=ChatAction.TYPING
    )

    try:
        async with action_sender:
            # генерация ответа на сообщение
            result = await nomadic_essen_conversator.generate_reply(message)
            # ответ на сообщение пользователю
            await message.answer(result['reply'], reply_markup=await extended_kb(example_buttons))
            return result

    except Exception as e:
        await report_error(
            message=message,
            bot=bot,
            bot_name=getattr(nomadic_essen_conversator, 'path')[5:],
            errors_channel_id=s.errors_channel_id,
            error=e,
            traceback_error_string=traceback.format_exc()
        )
