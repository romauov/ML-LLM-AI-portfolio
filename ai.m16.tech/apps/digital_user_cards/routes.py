"""
Веб сервис для создания цифровых карточек

@author Yaroslav Koltashev
"""
from os.path import join
import ast

from flask import Flask, jsonify, request
import pandas as pd

from . import blueprint


app = Flask(__name__)

def company(data_dict: dict) -> str:
    """
    Описание компании для пользователя
    
    Args:
        data_dict (dict): Словарь с информацией о пользователе. Ключи - названия столбцов

    Returns:
        str: Строка с описанием компании, в которой работает данных пользователь. 
            Если компании нет, возвращает Информации о компании нет
    """

    result = ""

    labels = {
        "Название:": "name_ru",
        "Описание:": "description_ru",
        "Вид деятельности:": "name_ru.1",
        "Место расположение:": "address_ru",
        "ИНН:": "company_inn",
        "Id региона:": "region_id"
    }

    if data_dict['user_id_meatinfo'] != 'пропуск':
        for key, value in labels.items():
            if key in ('ИНН:', 'Id региона:') and data_dict[value+'_meatinfo'] != 'пропуск':
                result += f"{key} {int(data_dict[value+'_meatinfo'])}".replace('\n', ' ')\
                    .replace('\r', '') + '\n'
            else:
                result += f"{key} {data_dict[value+'_meatinfo']}".replace('\n', ' ')\
                    .replace('\r', '') + '\n'

    if data_dict['user_id_fishretail'] != 'пропуск':
        for key, value in labels.items():
            if key in ('ИНН:', 'Id региона:') and data_dict[value+'_fishretail']!='пропуск':
                result += f"{key} {int(data_dict[value+'_fishretail'])}".replace('\n', ' ')\
                    .replace('\r', '') + '\n'
            else:
                result += f"{key} {data_dict[value+'_fishretail']}".replace('\n', ' ')\
                    .replace('\r', '') + '\n'

    if not result:
        result = 'Информации о компании нет'
    return result

def clear_dict(data_dict:dict) -> str:
    """
    Преобразование таблиц из dict в markdown

    Args:
        data_dict (dict): Словарь таблицы для  преобразования

    Returns:
        str: markdown срока в виде таблицы, иначе возвращается Информации отсутствует
    """
    # data_dict = data_dict #.replace('Timestamp(', '').replace(')', '')
    # pylint: disable=(bare-except)
    try:
        data_dict = pd.DataFrame(ast.literal_eval(data_dict)).to_markdown()
        return data_dict
    except:
        return "Информации отсутствует"


# @app.route('/', methods=['POST'])
@blueprint.route('/user_card', methods=['POST'])
def get_user_card():
    """
    Создание карточки пользователя
    
    Args:
        user_id (int): Id пользователя
    Returns:
        str: Карточка пользователя в виде строки с таблицами markdown
    """
    # pylint: disable=(bare-except)
    try:
        user_id = request.get_json()['user_id']
        # print(user_id)
    except:
        return jsonify({'Ошибка': 'Ключ user_id в полученных данных не найден'})

    data_card = pd.read_csv(join('apps', 'file_hosting','digital_user_cards', 'data_card.csv'))

    user = data_card[data_card['userId'] == user_id]
    if not user.empty:  # Проверка наличия пользователя в базе
        # Надо заменить пропуски значениями либо -1 либо "пропуск"

        # display(user.reset_index(drop = True).fillna('пропуск').T.to_dict()[0])
        # print(type(user.reset_index(drop = True).fillna('пропуск').T.to_dict()[0]['user_id_fishretail']))
        user = user.reset_index(drop = True).fillna('пропуск').T.to_dict()[0]

        card = f"""
userId: {user['userId']}  
ФИО: {user['lastname']} {user['firstname']}  
Должность: {user['position']}  
Активный ли пользователь: {user['is_active']}  
Дата последней активности: {user['last_action_date']}  
Дата регистрации: {user['dateCreated']}  
Id региона : {user['regionId']}

Компания  
{company(user)}  

Рассылка
Количество открытий рассылки: {user['count_open_email']}
Количество отправленных пользователю рассылок: {user['count_send_mail']}

Количество просмотренных объявлений на покупку: {user['watch_buy_count']}
Количество просмотренных объявлений на продажу: {user['watch_sale_count']}
Процент просмотренных объявлений на покупку: {user['watch_buy']}
Процент просмотренных объявлений на продажу: {user['watch_sale']}

Количество выставленных объявлений на покупку: {user['create_buy_count']}
Количество выставленных объявлений на продажу: {user['create_sale_count']}
Процент выставленных объявлений на покупку: {user['create_buy']}
Процент выставленных объявлений на продажу: {user['create_sale']}

Топ 5 самых популярных type1: {user['type1']}
Топ 5 самых популярных type2: {user['type2']}

Последние объявления пользователя
{clear_dict(user['advertisements'])}

Последняя активность
{clear_dict(user['last_action'])}
"""
        return jsonify({"card": card})

    return jsonify({'Ошибка': 'Такого пользователя нет в базе'})


if __name__ == '__main__':
    app.run(debug=True)
