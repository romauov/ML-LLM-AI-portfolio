import asyncio
import json
import os

from config.config import Config

cfg = Config.from_yaml()


async def get_user_dialog_history(user_id, reset_dialog_message):
    dialog_history = []
    dialog_file_path = os.path.join('user_dialog_history', f'{user_id}.txt')

    # Создаем файл, если он не существует, и читаем историю диалога из файла, используя мьютекс
    async with asyncio.Lock():
        _create_if_not_exist(dialog_file_path)

        # Читаем историю диалога из файла
        with open(dialog_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

            for line in reversed(lines):
                if len(dialog_history) >= cfg.count_history_messages:
                    break

                try:
                    record = json.loads(line)
                    role = record.get('role')

                    # читаем историю до сообщения обновления диалога
                    if role == 'assistant' and record.get('content') == reset_dialog_message:
                        break

                    elif role in {'user', 'assistant'}:
                        dialog_history.append(record)
                except json.JSONDecodeError:
                    continue
    return dialog_history[::-1]


async def save_user_dialog(user_id, role, message):
    dialog_file_path = os.path.join('user_dialog_history', f'{user_id}.txt')

    async with asyncio.Lock():
        _create_if_not_exist(dialog_file_path)

        with open(dialog_file_path, 'a', encoding='utf-8') as f:
            json_record = json.dumps({"role": role, "content": message}, ensure_ascii=False)
            f.write(json_record + '\n')


def _create_if_not_exist(path):
    if not os.path.exists(path):
        with open(path, 'w', encoding="utf-8"):
            pass
