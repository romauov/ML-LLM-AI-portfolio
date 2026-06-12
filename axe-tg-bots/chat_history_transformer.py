import os
import json
import sys

def convert_to_jsonlines(root_dir):
    """Конвертирует JSON-файлы в формат JSON Lines"""
    for root, _, files in os.walk(root_dir):
        for filename in files:
            if filename.lower().endswith('.json'):
                filepath = os.path.join(root, filename)
                try:
                    # Чтение файла с обработкой BOM
                    with open(filepath, 'r', encoding='utf-8-sig') as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError:
                            # Пропускаем файлы, которые не являются валидным JSON
                            continue
                    
                    # Проверяем, что это список словарей с нужными ключами
                    if not (isinstance(data, list) and 
                            all(isinstance(item, dict) for item in data)):
                        continue
                    
                    # Фильтруем записи с role и content
                    valid_records = [
                        item for item in data 
                        if 'role' in item and 'content' in item
                    ]
                    
                    if not valid_records:
                        print(f"Пропуск {filepath}: нет записей с role и content")
                        continue

                    with open(filepath, 'w', encoding='utf-8') as f:
                        for record in valid_records:
                            json_line = json.dumps(
                                record, 
                                ensure_ascii=False, 
                                separators=(',', ':')
                            )
                            f.write(json_line + '\n')
                    
                    print(f"Конвертирован: {filepath} ({len(valid_records)} записей)")
                
                except Exception as e:
                    print(f"Ошибка обработки {filepath}: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    logs_dir = 'logs'  # Основная папка с логами
    
    if not os.path.exists(logs_dir):
        print(f"Папка не найдена: {logs_dir}")
        sys.exit(1)
    
    print(f"Начало конвертации файлов в {logs_dir}")
    convert_to_jsonlines(logs_dir)
    print("Конвертация завершена!")