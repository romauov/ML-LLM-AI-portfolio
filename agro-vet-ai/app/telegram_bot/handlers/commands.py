import logging
from aiogram import Router, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from app.db.user_model import User


router = Router()


@router.message(Command("start"))
async def start_handler(message: Message, user_db: User) -> None:
    # Создаём инлайн-клавиатуру с кнопками
    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Я умею", callback_data="i_can")],
            [InlineKeyboardButton(text="А что писать?", callback_data="what_to_write")],
        ]
    )

    user_telegram_id = int(message.from_user.id)
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""

    try:
        existing_user = await user_db.user_by_telegram_id(user_telegram_id)

        if existing_user:
            logging.info(f"Пользователь уже зарегистрирован: ID={existing_user['id']}")
            await message.answer(
                f"С возвращением, <b><i>{existing_user['first_name']}</i></b>! 👋\n"
                f"Рад тебя снова видеть! 🚀",
                parse_mode="HTML",
                reply_markup=inline_keyboard
            )
        else:
            user_db_result = await user_db.create_user(user_telegram_id, username, first_name)
            logging.info(f"Новый пользователь добавлен: ID={user_db_result}")

            await message.answer(
                f"Привет, <b><i>{first_name}</i></b>! 👋\n"
                f"Ты успешно зарегистрирован в системе! 🚀",
                parse_mode="HTML",
                reply_markup=inline_keyboard
            )

    except Exception as e:
        logging.error(f"Ошибка при обработке команды /start: {e}")
        await message.answer("Произошла ошибка. Попробуй ещё раз позже. 😢")


# Обработчик кнопки "Я умею"
@router.callback_query(lambda c: c.data == "i_can")
async def i_can_handler(callback_query: types.CallbackQuery) -> None:
    # inline_keyboard = InlineKeyboardMarkup(
    #     inline_keyboard=[
    #         [InlineKeyboardButton(text="Диагностика заболеваний птиц", callback_data="avian_disease_diagnosis")],
    #         [InlineKeyboardButton(text="Информация о препаратах ГК ВИК", callback_data="drug_instruction_answers")],
    #     ]
    # )

    # await callback_query.message.answer(
    #         f"<b>Выбери раздел:</b>",
    #         parse_mode="HTML",
    #         reply_markup=inline_keyboard
    #     )

    await callback_query.message.answer(
        "Я могу ответить на вопросы по ветеринарии (заболевания кур, свиней), помочь интерпретировать результаты лабораторных исследований и консультировать по ветеринарным препаратам, опираясь на официальные инструкции ГК ВИК."
        "\n"
        "На данный момент моя база знаний по ветеринарии включает:\n"
        "1. Каталог ветеринарных препаратов «ВИК – здоровье животных» (сайт vicgroup.ru)\n"
        "2. Книги и руководства (используются для ответов на вопросы по заболеваниям птиц):\n"
        "   - Н.А. Татарникова — Болезни птиц. Учебное пособие (2023)\n"
        "   - Хлып Д.Н. — Атлас-пособие по нормальной и патологической анатомии и физиологии сельскохозяйственных птиц (2018)\n"
        "   - АгроФид — Кокцидиоз (2013)\n"
        "   - D. Herenda — Manual on meat inspection for developing countries (2000)\n"
        "3. Избранные онлайн-ресурсы (используются для ответов на вопросы по заболеваниям птиц):\n"
        "   - русскоязычный сайт MSD Animal Health: msd-animal-health-poultry.ru\n"
        "   - MSD Veterinary Manual: msdvetmanual.com\n"
        "   - ВОЗЖ — Руководство по наземным животным: rr-europe.woah.org\n"
        "\n"
        "Задавайте интересующие вас вопросы!\n"
    )

    await callback_query.answer()  # Закрываем уведомление


# Обработчик кнопки "А что писать?"
@router.callback_query(lambda c: c.data == "what_to_write")
async def what_to_write_handler(callback_query: types.CallbackQuery) -> None:
    await callback_query.message.answer(
        "Понимаю, не всегда сразу понятно, что писать в бот. "
        "Начните с чего-нибудь, о чем спрашивают клиенты о ваших препаратах, и я постараюсь помочь."
    )
    await callback_query.answer()  # Закрываем уведомление


@router.callback_query(lambda c: c.data == "drug_instruction_answers")
async def drug_instructions_handler(callback_query: types.CallbackQuery) -> None:
    await callback_query.message.answer("Отвечу на вопросы по препаратам.")


@router.callback_query(lambda c: c.data == "avian_disease_diagnosis")
async def avian_diseases_handler(callback_query: types.CallbackQuery) -> None:
    await callback_query.message.answer("Отвечу на вопросы по заболеваниям.")
