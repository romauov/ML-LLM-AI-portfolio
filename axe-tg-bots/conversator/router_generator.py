import traceback

from aiogram import Bot, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

from conversator.conversator import Conversator
from utils.aiogram_keyboards import extended_kb
from utils.errors import report_error
from utils.logger import logger as log

def generate_router(client_data) -> Router:
    router = Router()
    conversator = Conversator(client_data)

    @router.message(CommandStart())
    async def send_welcome(message: Message):
        action_sender = ChatActionSender(
            bot=message.bot,
            chat_id=message.chat.id,
            action=ChatAction.TYPING
        )
        async with action_sender:
            result = await conversator.generate_reply(message)
            await message.answer(
                result['reply'],
                reply_markup=await extended_kb(conversator.buttons,
                                               conversator.placeholder)
            )

    @router.message(Command('update'))
    async def update_instructions(message: Message):
        conversator.update()
        await message.answer('Инструкции обновлены.')

    @router.message()
    async def generate_reply_message(message: Message, bot: Bot):
        try:
            await message.forward(chat_id=client_data.channel_id)
            action_sender = ChatActionSender(
                bot=message.bot,
                chat_id=message.chat.id,
                action=ChatAction.TYPING
            )
            async with action_sender:
                result = await conversator.generate_reply(message)
                await message.answer(
                    result['reply'],
                    reply_markup=await extended_kb(conversator.buttons,
                                                   conversator.placeholder)
                )
                await bot.send_message(
                    chat_id=client_data.channel_id, 
                    text=result['reply']
                    )
                if 'message_for_manager' in result and result['message_for_manager']:
                    for manager in client_data.manager_ids:
                        try:
                            await message.forward(chat_id=manager)
                            await bot.send_message(
                                chat_id=manager,
                                text=await conversator.make_summary(message.from_user.id)
                            )
                        except:
                            pass
                
        except Exception as e:
            log.error(f"Error generating reply: {e}")
            await report_error(message=message,
                               bot=bot,
                               bot_name=client_data.client_name,
                               errors_channel_id='@m16_tg_errors_channel',
                               error=e,
                               traceback_error_string=traceback.format_exc()
                               )

    return router