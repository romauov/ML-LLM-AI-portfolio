"""
обработчик сообщений aiogram

@author Sergei Romanov
"""
import traceback
from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.chat_action import ChatActionSender
from aiogram.types import Message, FSInputFile, ContentType
from clients.muksun.keyboards import example_buttons
from clients.muksun.conversator_muksun import ConversatorMuksun
from utils.aiogram_keyboards import extended_kb, model_kb
from utils.decorators import forward_and_send_message
from utils.settings import secrets as s
from utils.traceback_error_log import report_error


class ModelUpdate(StatesGroup):
    model = State()


muksun_conversator = ConversatorMuksun(
    table_id=None,
    text_id=s.muksun.reglament,
    name='muksun',
    model='gpt-4o-mini')

muksun_router = Router()


@muksun_router.message(CommandStart())
async def send_welcome(message: Message):
    """обработка команды старт

    Args:
        message (Message): telegram message object
    """
    await message.answer("Здравствуйте! Я готов ответить на вопросы. Что вас интересует?",
                         reply_markup=await extended_kb(example_buttons))


@muksun_router.message(F.text == 'Выслать прайс')
@forward_and_send_message(s.muksun.channel_id, s.muksun.manager_ids, muksun_conversator)
async def query_options(message: Message, bot: Bot):
    """обработка запроса отправки прайс-листа

    Args:
        message (Message): telegram message object
    """
    reply = 'Вот наш актуальный прайс-лист по продукции в наличии, чем я ещё могу быть полезен?'
    await message.answer(reply, reply_markup=await extended_kb(example_buttons))
    await message.answer_document(FSInputFile(path='logs/muksun/price_list.xls'))
    return {"reply": reply}


@muksun_router.message(Command('update'))
async def update_instructions(message: Message):
    """ обработка команды для обновления промта

    Args:
        message (Message): telegram message object
    """
    muksun_conversator.update()
    await message.answer('Инструкции обновлены.')


@muksun_router.message(F.content_type == ContentType.DOCUMENT)
async def handle_document(message: Message, bot: Bot):
    """ обработка сообщения с вложенным excel файлом для обновления прайса

    Args:
        message (Message): telegram message object
    """
    if message.from_user.id not in s.muksun.admin_ids:
        await message.reply(f"У вас нет прав для выполнения этой команды.")
        return

    document = message.document

    if document.mime_type == 'application/vnd.ms-excel':
        file_id = document.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file = await bot.download_file(file_path)

        with open("logs/muksun/price_list.xls", "wb") as f:
            f.write(file.read())
        try:
            muksun_conversator.update()
        except:
            await message.answer("Пожалуйста отправьте файл прежнего формата")
        await message.answer("Прайс-лист обновлён.")
    else:
        await message.answer("Пожалуйста, отправьте файл в формате Excel (.xls).")


@muksun_router.message(Command('model'))
async def change_model(message: Message, state: FSMContext):
    if message.from_user.id not in s.muksun.admin_ids:
        await message.reply(f"У вас нет прав для выполнения этой команды.")
        return
    await state.set_state(ModelUpdate.model)
    await message.answer("Выберите модель из списка", reply_markup=await model_kb())


@muksun_router.message(ModelUpdate.model)
async def set_model(message: Message, state: FSMContext):
    # await state.update_data(model=message.text)
    # data = await state.get_data()
    muksun_conversator.change_model(message.text.split(' ', maxsplit=1)[0])
    await message.answer(f'Установлена модель {getattr(muksun_conversator, "model")}',
                         reply_markup=await extended_kb(example_buttons))
    await state.clear()


@muksun_router.message()
@forward_and_send_message(s.muksun.channel_id, s.muksun.manager_ids, muksun_conversator)
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
            result = await muksun_conversator.generate_reply(message)
            # ответ на сообщение пользователю
            await message.answer(result['reply'],
                                 reply_markup=await extended_kb(example_buttons),
                                 )
            if 'send_price' in result and result['send_price']:
                await message.answer_document(FSInputFile(path='logs/muksun/price_list.xls'))

            return result

    except Exception as e:
        await report_error(message=message,
                           bot=bot,
                           bot_name=getattr(muksun_conversator, 'path')[5:],
                           errors_channel_id=s.errors_channel_id,
                           error=e,
                           traceback_error_string=traceback.format_exc())
