import os
import shutil
import telebot
import time
import traceback

from requests.exceptions import ConnectionError, ReadTimeout
from telebot import types
from telebot.apihelper import ApiTelegramException

from app.meat.utils.data import errors_folder as errors_folder_meat
from app.meat.utils.data import processed_folder as processed_folder_meat
from app.meat.utils.data import source_folder as source_folder_meat
from app.meat.utils.data import subfolders as subfolders_meat
from app.fishes.data import errors_folder as error_folder_fish
from app.fishes.data import processed_folder as processed_folder_fish
from app.fishes.data import source_folder as source_folder_fish
from app.fishes.data import subfolders as subfolders_fish
from app.utils.logger import logger as log, log_traceback
from app.utils.settings import secrets as s


bot = telebot.TeleBot(s.tg_token)


def send_notification(file_path, file, count, err_msg):
    try:
        with open(file_path, 'rb') as f:
            if not err_msg:
                if count == 1:
                    bot.send_message(s.notifications_channel,
                                     f"Успешно обработан: {file}")
                elif count > 1:
                    bot.send_document(s.notifications_channel,
                                      f,
                                      caption=f'Данный файл обработан {count} раз(а)')
            else:
                bot.send_document(s.notifications_channel,
                                  f,
                                  caption=f"!!!Ошибка при обработке файла!!!\n{err_msg}")

    except Exception as e:
        log.error(f"Ошибка при отправке уведомления: {e}")


def start_bot_polling():
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message: types.Message):
        bot.reply_to(
            message,
            "Привет, это бот для работы с мониторингами Комиды, доступные команды:\n"
            "/meat_errors - команда для вывода списка файлов с ошибками при обработке\n"
            "/meat_processed - команда для вывода успешно обработанных файлов\n"
            "/retry_meat - команда для повторной обработки файлов с ошибками\n"
            "/fish_errors - команда для вывода списка файлов с ошибками при обработке\n"
            "/fish_processed - команда для вывода успешно обработанных файлов\n"
            "/retry_fish - команда для повторной обработки файлов с ошибками"
        )

# meat ========================================================================

    @bot.message_handler(commands=['meat_errors'])
    def send_meat_errors(message: types.Message):
        report = "Список мониторингов с ошибками при обработке:"
        for root, _, files in os.walk(errors_folder_meat):
            if os.path.basename(root) in subfolders_meat:
                for file in files:
                    if file.endswith('.xlsx') or file.endswith('.xls'):
                        report += f'\n{os.path.basename(file)}'
        bot.reply_to(message, report)

    @bot.message_handler(commands=['meat_processed'])
    def see_processed_meat(message: types.Message):
        report = "Список обработанных мониторингов:"
        for root, _, files in os.walk(processed_folder_meat):
            if os.path.basename(root) in subfolders_meat:
                for file in files:
                    if file.endswith('.xlsx') or file.endswith('.xls'):
                        report += f'\n{os.path.basename(file)}'
        bot.reply_to(message, report)

    @bot.message_handler(commands=['retry_meat'])
    def retry_meat_errors(message: types.Message):
        for root, _, files in os.walk(errors_folder_meat):
            source_fldr = os.path.join(source_folder_meat, os.path.basename(root))
            if os.path.basename(root) in subfolders_meat:
                for file in files:
                    if file.endswith('.xlsx') or file.endswith('.xls'):
                        shutil.move(os.path.join(root, file),
                                    os.path.join(source_fldr, file))
        bot.reply_to(message, "Повторная попытка обработки")

# fish ========================================================================

    @bot.message_handler(commands=['fish_errors'])
    def send_fish_errors(message: types.Message):
        report = "Список мониторингов с ошибками при обработке:"
        for root, _, files in os.walk(error_folder_fish):
            if os.path.basename(root) in subfolders_fish:
                for file in files:
                    if file.endswith('.xlsx') or file.endswith('.xls'):
                        report += f'\n{os.path.basename(file)}'
        bot.reply_to(message, report)

    @bot.message_handler(commands=['fish_processed'])
    def see_processed_fish(message: types.Message):
        report = "Список обработанных мониторингов:"
        for root, _, files in os.walk(processed_folder_fish):
            if os.path.basename(root) in subfolders_fish:
                for file in files:
                    if file.endswith('.xlsx') or file.endswith('.xls'):
                        report += f'\n{os.path.basename(file)}'
        bot.reply_to(message, report)

    @bot.message_handler(commands=['retry_fish'])
    def retry_fish_errors(message: types.Message):
        for root, _, files in os.walk(error_folder_fish):
            source_fldr = os.path.join(source_folder_fish, os.path.basename(root))
            if os.path.basename(root) in subfolders_fish:
                for file in files:
                    if file.endswith('.xlsx') or file.endswith('.xls'):
                        shutil.move(os.path.join(root, file),
                                    os.path.join(source_fldr, file))
        bot.reply_to(message, "Повторная попытка обработки")

# cycle =======================================================================
    retry_count = 0
    max_retries = 100
    
    while True:
        try:
            log.info(f"Попытка запуска бота (попытка {retry_count + 1}/{max_retries})")
            bot.infinity_polling(timeout=90, long_polling_timeout=5)
            
        except KeyboardInterrupt:
            log.info("Бот остановлен пользователем")
            break
            
        except ReadTimeout:
            log.info("Перезапуск polling из-за ReadTimeout...")
            time.sleep(1)

        except ApiTelegramException as e:
            if e.error_code == 429:
                retry_after = e.result_json.get('parameters', {}).get('retry_after', 5)
                log.warning(f"Telegram API rate limit (429). Retrying after {retry_after} seconds.")
                time.sleep(retry_after + 1)
            elif e.error_code >= 500:
                log.warning(f"Telegram server error ({e.error_code}). Retrying in 15 seconds.")
                time.sleep(15)
            else:
                log.error(f"Необработанная ошибка Telegram API: {str(e)}")
                log_traceback(traceback.format_exc(), e)
                break

        except ConnectionError as ce:
            retry_count += 1
            log.error(f"Сетевая ошибка: {str(ce)}")
            if retry_count >= max_retries:
                log.error("Достигнуто максимальное количество попыток")
                break
                
            sleep_time = 60 * retry_count
            log.info(f"Повторная попытка через {sleep_time} секунд...")
            time.sleep(sleep_time)
            
        except Exception as e:
            log.error(f"Критическая ошибка: {str(e)}")
            log_traceback(traceback.format_exc(), e)
            break
            
    log.info("Работа бота завершена")

