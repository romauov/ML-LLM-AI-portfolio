"""
логирование затрат Chat GPT

@author Sergei Romanov
"""
import csv
import json
import time
import os
    
def log_charges(path, from_id, model, process, input_tokens, output_tokens):
    """логирование затрат

    Args:
        path (str): путь к логу
        from_id (int): id клиента в телеграм
        model (str): название модели Chat GPT
        process (str): 'text_generation', 'functions', 'pick products' or 'summary'
        input_tokens (int): количество промт-токенов
        output_tokens (int): количество сгенерированных токенов
    """
    with open('model_rates.json') as f:
        model_charges = json.load(f)

    input_rate = model_charges[model][0]
    output_rate = model_charges[model][1]
    charge = input_tokens * input_rate + output_tokens * output_rate

    csv_file = f'{path}/charges.csv'
    timestamp = time.strftime("%c")

    headers = ['timestamp', 'from_id', 'model', 'process', 'input_tokens', 'output_tokens', 'charge']
    new_data = [timestamp, from_id, model, process, input_tokens, output_tokens, charge]

    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)

    with open(csv_file, 'a+', newline='') as file:
        csv_writer = csv.writer(file)
        new_data = [timestamp, from_id, model, process, input_tokens, output_tokens, charge]
        csv_writer.writerow(new_data)
