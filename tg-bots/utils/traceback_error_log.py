import time

def split_text(text, max_length=4000):
    """Функция для разбиения строки на фрагменты не более заданного размера

    Args:
        text (str): текст сообщения
        max_length (int, optional): Лимит длины сообщения в телеграм (4096).

    Returns:
        List: список с фрагментами сообщений
    """
    chunks = []
    current_string = text
    while len(current_string) > max_length:
        i = max_length
        while current_string[i] != '\n' and i != 0:
            i -= 1
        if i != 0:
            current_string = current_string[:i]
            text = text[i+1:]
        else:
            current_string = current_string[:max_length]
            text = text[max_length +1:]        
        chunks.append(current_string)
        current_string = text
    chunks.append(current_string)
    return chunks

def log_traceback(traceback_error_string, error, message=''):
    """запись трейсбэка с ошибкой в лог

    Args:
        traceback_error_string (str): traceback
        error (Exception, optional): вид ошибки. Defaults to ''.
        message (str, optional): текст сообщения, приведшего к ошибке. Defaults to ''.
    """
    with open("logs/errors.log", "a") as myfile:
        myfile.write("\r\n\r\n" + 
                     time.strftime("%c") + 
                     "\r\n<<ERROR>>\r\n" + 
                     f'{error}' + 
                     "\r\n<<TRACEBACK>>\r\n" + 
                     traceback_error_string + 
                     "\r\n<<MESSAGE>>\r\n" + 
                     message)

async def report_error(message, bot, bot_name, errors_channel_id, error, traceback_error_string):
    """отправка сообщений об ошибке и её логирование

    Args:
        message  (Message): telegram message object
        bot (Bot): telegram bot object
        bot_name (str): имя бота
        errors_channel_id (str): адрес телеграм-канала с ошибками
        error (Exception, optional): вид ошибки.
        traceback_error_string (str): traceback
    """
    await message.answer(f"Произошла ошибка, попробуйте позже!")
    # пересылка админу сообщения, на котором возникла ошибка
    await message.forward(chat_id=errors_channel_id)
    # отправка сообщений об ошибке админу
    await bot.send_message(
        chat_id=errors_channel_id,
        text=f"{bot_name}\n" + \
            "==============\n\n" + \
                f'{error}'
                )
    traceback_chunks = split_text(traceback_error_string)
    for chunk in traceback_chunks:
        await bot.send_message(
            chat_id=errors_channel_id,
            text=f"""
            ```sh
            {chunk}
            ```
            """
        )
    # логирование ошибки
    log_traceback(
        error=error,
        traceback_error_string=traceback_error_string, 
        message=f"bot_name: {bot_name}\t" + f"tg_id: {message.chat.id}\t" + f"text: {message.text}"
    )