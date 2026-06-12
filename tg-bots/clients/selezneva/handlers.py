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
from clients.selezneva.keyboards import example_buttons, price_buttons
from clients.selezneva.conversator_selezneva import ConversatorSelezneva
from utils.aiogram_keyboards import extended_kb, model_kb
from utils.decorators import forward_and_send_message
from utils.settings import secrets as s
from utils.traceback_error_log import report_error


class ModelUpdate(StatesGroup):
    model = State()


selezneva_conversator = ConversatorSelezneva(
    table_id=s.selezneva.price_id,
    text_id=s.selezneva.reglament,
    name='selezneva',
    model='gpt-4o-mini')

selezneva_router = Router()


@selezneva_router.message(CommandStart())
async def send_welcome(message: Message):
    """обработка команды старт

    Args:
        message (Message): telegram message object
    """
    await message.answer("Здравствуйте! Я готов ответить на вопросы. Что вас интересует?",
                         reply_markup=await extended_kb(example_buttons))


@selezneva_router.message(F.text == 'Выслать прайс')
@forward_and_send_message(s.selezneva.channel_id, s.selezneva.manager_ids, selezneva_conversator)
async def choose_price(message: Message, bot: Bot):
    """обработка запроса отправки прайс-листа

    Args:
        message (Message): telegram message object
    """
    reply = 'Какой прайс-лист вас интересует, на рыбу или снэки?'
    await message.answer(reply, reply_markup=await extended_kb(price_buttons))
    return {"reply": reply}


@selezneva_router.message(F.text == 'Прайс-лист на рыбу, филе и икру')
@forward_and_send_message(s.selezneva.channel_id, s.selezneva.manager_ids, selezneva_conversator)
async def send_fish_price(message: Message, bot: Bot):
    """обработка запроса отправки прайс-листа

    Args:
        message (Message): telegram message object
    """
    reply = 'Вот наш актуальный прайс-лист по рыбе в наличии, чем я ещё могу быть полезен?'
    await message.answer(reply, reply_markup=await extended_kb(example_buttons))
    await message.answer_document(FSInputFile(path='logs/selezneva/pricelist_selezneva_fish.xlsx'))
    return {"reply": reply}


@selezneva_router.message(F.text == 'Прайс-лист на рыбные снеки')
@forward_and_send_message(s.selezneva.channel_id, s.selezneva.manager_ids, selezneva_conversator)
async def send_snacks_price(message: Message, bot: Bot):
    """обработка запроса отправки прайс-листа

    Args:
        message (Message): telegram message object
    """
    reply = 'Вот наш актуальный прайс-лист по снэкам в наличии, чем я ещё могу быть полезен?'
    await message.answer(reply, reply_markup=await extended_kb(example_buttons))
    await message.answer_document(FSInputFile(path='logs/selezneva/pricelist_selezneva_snacks.docx'))
    return {"reply": reply}


@selezneva_router.message(F.text == 'Оба')
@forward_and_send_message(s.selezneva.channel_id, s.selezneva.manager_ids, selezneva_conversator)
async def send_both_prices(message: Message, bot: Bot):
    """обработка запроса отправки прайс-листа

    Args:
        message (Message): telegram message object
    """
    reply = 'Вот наш актуальный прайс-лист по рыбе и снэкам в наличии, чем я ещё могу быть полезен?'
    await message.answer(reply, reply_markup=await extended_kb(example_buttons))
    await message.answer_document(FSInputFile(path='logs/selezneva/pricelist_selezneva_fish.xlsx'))
    await message.answer_document(FSInputFile(path='logs/selezneva/pricelist_selezneva_snacks.docx'))
    return {"reply": reply}


@selezneva_router.message(Command('update'))
async def update_instructions(message: Message):
    """ обработка команды для обновления промта

    Args:
        message (Message): telegram message object
    """
    selezneva_conversator.update()
    await message.answer('Инструкции обновлены.')


@selezneva_router.message(Command('model'))
async def change_model(message: Message, state: FSMContext):
    if message.from_user.id not in s.selezneva.admin_ids:
        await message.reply(f"У вас нет прав для выполнения этой команды.")
        return
    await state.set_state(ModelUpdate.model)
    await message.answer("Выберите модель из списка", reply_markup=await model_kb())


@selezneva_router.message(F.content_type == ContentType.DOCUMENT)
async def handle_document(message: Message, bot: Bot):
    """ обработка сообщения с вложенным excel файлом для обновления прайса

    Args:
        message (Message): telegram message object
    """
    if message.from_user.id not in s.selezneva.admin_ids:
        await message.reply(f"У вас нет прав для выполнения этого действия.")
        return

    document = message.document

    if document.mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        file_id = document.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path
        file = await bot.download_file(file_path)

        with open("logs/selezneva/pricelist_selezneva_snacks.docx", "wb") as f:
            f.write(file.read())

        try:
            selezneva_conversator.update()
        except:
            await message.answer("Произошла ошибка при обновлении. Пожалуйста, отправьте файл в правильном формате.")

        await message.answer("Прайс-лист обновлён.")
    else:
        await message.answer("Пожалуйста, отправьте файл в формате Word (.docx).")


@selezneva_router.message(ModelUpdate.model)
async def set_model(message: Message, state: FSMContext):
    # await state.update_data(model=message.text)
    # data = await state.get_data()
    selezneva_conversator.change_model(message.text.split(' ', maxsplit=1)[0])
    await message.answer(f'Установлена модель {getattr(selezneva_conversator, "model")}',
                         reply_markup=await extended_kb(example_buttons))
    await state.clear()


@selezneva_router.message()
@forward_and_send_message(s.selezneva.channel_id, s.selezneva.manager_ids, selezneva_conversator)
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
            result = await selezneva_conversator.generate_reply(message)
            # ответ на сообщение пользователю
            await message.answer(result['reply'],
                                 reply_markup=await extended_kb(example_buttons),
                                 )
            if 'send_price' in result and result['send_price']:
                await message.answer_document(FSInputFile(path='logs/selezneva/price_list_IP_Selezneva.xlsx'))

            return result

    except Exception as e:
        await report_error(message=message,
                           bot=bot,
                           bot_name=getattr(selezneva_conversator, 'path')[5:],
                           errors_channel_id=s.errors_channel_id,
                           error=e,
                           traceback_error_string=traceback.format_exc())
