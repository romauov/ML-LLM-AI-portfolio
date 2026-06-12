"""
функции для работы с историей чата

@author Sergei Romanov
"""
import os
import json

def get_history(path, from_id, n_messages=10):
    """ получение истории сообщений из файла в формате JSON Lines """
    filename = os.path.join(path, f"{from_id}.json")
    user_records = []
    
    if not os.path.exists(filename):
        return []
    
    try:
        # Читаем все строки файла
        with open(filename, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        # Обрабатываем строки в обратном порядке
        for line in reversed(lines):
            if len(user_records) >= n_messages:
                break
                
            try:
                record = json.loads(line)
                if record.get('role') in {'user', 'assistant'}:
                    user_records.append(record)
            except json.JSONDecodeError:
                continue  # Пропускаем битые записи
        
        # Возвращаем в правильном порядке (от старых к новым)
        return user_records[::-1]
    
    except Exception as e:
        print(f"Error reading {filename}: {str(e)}")
        return []


def write_history(path, from_id, data):
    if from_id is None:
        return

    filename = f'{path}/{from_id}.json'

    with open(filename, 'a', encoding='utf-8-sig') as file:
        json_record = json.dumps(data, ensure_ascii=False)
        file.write(json_record + '\n')

