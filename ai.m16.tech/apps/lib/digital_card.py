"""
Метод для предобработки  и получения данных через SQL запросы

@author Yaroslav Koltashev
"""
import pandas as pd

from .db import create_client_ch, create_connect_db_m16_stage


def top_5(df: pd.DataFrame, col: str):
    """
    Генерирует DataFrame, содержащий пять наиболее часто встречающихся значений указанного столбца
      для каждого уникального пользователя во входном DataFrame.
    
    Параметры:
    - df: pd.DataFrame - Входной DataFrame.
    - col: str - Имя столбца, для которого нужно найти пять наиболее часто встречающихся значений. (type1, type2)
    
    Возвращает:
    - pd.DataFrame - DataFrame с двумя столбцами: 'userId' и 'col', где 'userId' содержит уникальные 
        идентификаторы пользователей, а 'col' содержит список пяти наиболее часто встречающихся значений 
        указанного столбца для каждого пользователя.
    """
    data = {"userId": [], col: []}
    for user in df['userId'].unique():
        data['userId'].append(user)
        val = df[(df['userId'] == user)][col].value_counts(
            normalize=True).index[:5]
        data[col].append(list(val))
    return pd.DataFrame(data)


def create_action(x: str, table: pd.DataFrame):
    """
	Создает действие на основе указанного user_id пользователя и таблицы.

	:param x: user_id пользователя.
	:type x: int

	:param table: Входная таблица.
	:type table: pandas.DataFrame

	:return: Словарь, содержащий дату, тип, заголовок и метку пяти верхних действий для указанного user_id пользователя,
      или строку 'нет данных', если действия не найдены.
	:rtype: Union[dict, str]

	"""

    table_copy = table[
        (table['userId'] == x)
    ].sort_values(by=['dateEvent'], ascending=False).iloc[:5].copy()

    table_copy['dateEvent'] = table_copy['dateEvent'].dt.strftime('%Y-%m-%d')
    table_copy = table_copy.fillna('пропуск')
    if not table_copy.empty:
        return table_copy[['dateEvent', 'type', 'title', 'label']].reset_index(drop=True).to_dict()
    return 'нет данных'


def crate_advertisements(x: str, table: pd.DataFrame):
    """
    Генерирует 5 последних объявлений для указанного пользователя.

    Параметры:
        x (str): Идентификатор пользователя.
        table (pd.DataFrame): Таблица, содержащая данные пользователя.

    Возвращает:
        dict: Словарь, содержащий пять последних объявлений пользователя, отсортированных по дате создания.
          Колонка 'itemId' удалена из результата.
        str: Если объявления не найдены, возвращает строку 'нет данных'.
    """
    temp_table = table[table['userId'] == x].sort_values(
        by=['dateCreated'], ascending=False).iloc[:5]

    temp_table = temp_table.fillna('пропуск')
    if not temp_table.empty:
        return temp_table.drop(columns=['itemId']).reset_index(drop=True).to_dict()
    return 'нет данных'


def user_stat():
    """
    Получение таблицы user_stat за 1 год

    return columns: userId, site, type, dateEvent
    """

    client = create_client_ch()
    sql = """
    WITH 
    -- Получение id которые имеют позицию (Там есть пустые строки в позиции) 
    good_id AS (SELECT userId, count(position) as count_pos
            FROM axe.userProfile
            GROUP BY userId
            having (count_pos = 1)),
            
                
    -- user stat без людей которые заходили на свои объявления          
    user_stat AS (SELECT
                    userId, itemId, site, type, dateEvent
                    FROM axe.userStat
                    WHERE userId in (SELECT userId FROM good_id)
                    AND datetimeEvent > toString(date_sub(YEAR, 1, now())))

    SELECT *
    FROM user_stat
    """
    items = client.execute(sql)

    return items


def user_stat_buy_sale():
    """
    Получение таблицы user_stat и таблицы tradeboard с действиями crate_buy, create_sale

    return columns: userId, site, type, dateEvent
    """

    client = create_client_ch()
    sql = """
    WITH 
    -- Получение id которые имеюют позицию (Там есть пустые строки в позиции) 
    good_id AS (SELECT userId, count(position) as count_pos
            FROM axe.userProfile
            GROUP BY userId
            having (count_pos = 1)),
                
                
    -- user stat без людей которые заходили на свои объявления          
    user_stat AS (SELECT
                    userId, itemId, site, type, dateEvent
                    FROM axe.userStat
                    WHERE type in ('create_buy', 'create_sale')
                    AND userId in (SELECT userId FROM good_id)
                    AND datetimeEvent > toString(date_sub(YEAR, 1, now())))


    SELECT *
    FROM user_stat
    """
    items = client.execute(sql)

    return items


def create_name_id_data_position():
    """
    Блок в схеме с полями ФИО, id, должность, дата создания аккаунта, id региона

    return columns: userId , position, firstname, lastname, dateCreated, regionId
    """
    client = create_client_ch()

    sql = """
    WITH 
    -- первый подзапрос с псевдонимом 
    good_id AS (SELECT userId, count(position) as count_pos
            FROM axe.userProfile
            GROUP BY userId
            having (count_pos = 1))

    -- userId , position, firstname, lastname
    SELECT userId , position, firstname, lastname, dateCreated, regionId
    from axe.userProfile
    INNER JOIN good_id ON userProfile.userId = good_id.userId
    WHERE position <> ''
    """

    items = client.execute(sql)

    return items

# Спросить
def create_company():
    """
    Получение информации о компаниях и базы данных Catalogue

    return columns: company_id, name_ru, description_ru, name_ru, address_ru, company_inn, region_id
    """
    db = create_connect_db_m16_stage()
    cursor = db.cursor()

    sql = """
    select comp2type.company_id, copm.name_ru, copm.description_ru, t.name_ru, ad.address_ru, copm.company_inn, copm.region_id
    FROM catalogue.company2type comp2type
    INNER join catalogue.type t ON comp2type.type_id = t.id
    INNER JOIN catalogue.address ad ON comp2type.company_id = ad.company_id
    INNER JOIN catalogue.company copm ON comp2type.company_id = copm.id
    """

    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    return data


def create_count_send_open():
    """
    Получение количества отправленных и открытых писем для каждого id за период с 1 год

    return columns: user_id, count_send_mail, count_open_email, email
    """
    db = create_connect_db_m16_stage()
    cursor = db.cursor()

    sql = """
    SELECT log.user_id, log.count_send_mail, email_os.count_open_email, email.email
    FROM (SELECT email_id as user_id, count(message_id) as count_send_mail
        FROM emailer.log
        WHERE id > 37171618
        GROUP BY user_id) as log
    INNER JOIN emailer.email ON log.user_id = email.id
    INNER JOIN (SELECT user_id, count(message_id) as count_open_email
                FROM emailer.email_open_stat
                WHERE dateadd > DATE_SUB(NOW(), INTERVAL 1 YEAR)
                GROUP BY user_id) as email_os ON email_os.user_id = log.user_id
    ORDER BY user_id
    """
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    return data


def create_type1_type2():
    """
    Получение type1 и type2 для каждого пользователя за период с 1 год

    return columns: userId, title, type1, type2
    """

    client = create_client_ch()
    sql = """
    WITH 
    -- Получение id которые имеюют позицию (Там есть пустые строки в позиции) 
    good_id AS (SELECT userId, count(position) as count_pos
            FROM axe.userProfile
            GROUP BY userId
            having (count_pos = 1)),
                
    -- user stat без людей которые заходили на свои объявления          
    user_stat AS (SELECT
                    userId, itemId, type
                    FROM axe.userStat
                    WHERE userId IN (SELECT userId FROM good_id)
                    -- AND(userId, itemId) NOT IN (SELECT userId, itemId FROM bad_id)
                    AND type IN ('watch_sale', 'watch_buy', 'create_sale', 'create_buy', 'create_up_sale', 'create_up_buy', 'edit_up_sale', 'edit_up_buy')
                    AND dateEvent > date_sub(YEAR, 1, now()))

    SELECT 
    userId,
    title,
    type1,
    type2
    FROM user_stat
    INNER JOIN axe.tradeboard ON tradeboard.itemId = user_stat.itemId
    """

    items = client.execute(sql)

    return items


def create_last_actions():
    """
    Получение последней активности для всех пользователей

    return columns: userId, last_action_date
    """
    client = create_client_ch()

    sql = """
    WITH 
    -- Получение id которые имеюют позицию (Там есть пустые строки в позиции) 
    good_id AS (SELECT userId, count(position) as count_pos
            FROM axe.userProfile
            GROUP BY userId
            having (count_pos = 1)),

    -- user stat без людей которые заходили на свои объявления          
    user_stat AS (SELECT
                    userId, itemId, dateEvent
                    FROM axe.userStat
                    WHERE userId IN (SELECT userId FROM good_id))

    SELECT userId, MAX(dateEvent) AS last_action_date
    FROM user_stat
    GROUP BY userId
    """

    items = client.execute(sql)

    return items


def watch_buy_sale():
    """
    Получение процентов просмотров объявлений на продажу / покупку для каждого пользователя

    return columns: userId, watch_sale, watch_buy, watch_sale_count, watch_buy_count
    """

    client = create_client_ch()
    sql = """
    WITH 
    -- пользователи, которые заходили на свои объявления и также которых нет в хороших id 
    bad_id AS (SELECT 
                userId,
                itemId
                FROM axe.tradeboard
                INNER JOIN axe.userStat ON tradeboard.userId = userStat.userId AND tradeboard.itemId = userStat.itemId),
                
    -- user stat без людей которые заходили на свои объявления          
    user_stat AS (SELECT
                    userId, itemId, site, type
                    FROM axe.userStat
                    WHERE (userId, itemId) NOT IN (SELECT userId, itemId FROM bad_id))        

    -- Получение процентов просмотров объявления на продажу и покупку

    SELECT userId,
        ((100*sale_count)/(sale_count+buy_count)) AS watch_sale,
        ((100*buy_count)/(sale_count+buy_count)) AS watch_buy,
        sale_count AS watch_sale_count,
        buy_count AS watch_buy_count
    FROM (SELECT userId,
        SUM(CASE WHEN type = 'watch_sale' THEN 1 ELSE 0 END) AS sale_count,
        SUM(CASE WHEN type = 'watch_buy' THEN 1 ELSE 0 END) AS buy_count
    FROM user_stat
    GROUP BY userId)

    """
    items = client.execute(sql)

    return items


def create_buy_sale():
    """
    Проценты выставленных объявлений на покупку/продажу

    return columns: userId, create_sale, create_buy, create_sale_count, create_buy_count
    """

    client = create_client_ch()
    sql = """
    WITH 
    -- пользователи, которые заходили на свои объявления и также которых нет в хороших id 
    bad_id AS (SELECT 
                userId,
                itemId
                FROM axe.tradeboard
                INNER JOIN axe.userStat ON tradeboard.userId = userStat.userId AND tradeboard.itemId = userStat.itemId),
                
    -- user stat без людей которые заходили на свои объявления          
    user_stat AS (SELECT
                    userId, itemId, site, type
                    FROM axe.userStat
                    WHERE (userId, itemId) NOT IN (SELECT userId, itemId FROM bad_id))        

    -- Получение процентов выставленных объявления на продажу и покупку

    SELECT userId,
        (100*sale_count)/(sale_count+buy_count) AS create_sale,
        (100*buy_count)/(sale_count+buy_count) AS create_buy,
        sale_count AS create_sale_count,
        buy_count AS create_buy_count
    FROM (SELECT userId,
        SUM(CASE WHEN type = 'create_sale' THEN 1 ELSE 0 END) AS sale_count,
        SUM(CASE WHEN type = 'create_buy' THEN 1 ELSE 0 END) AS buy_count
    FROM user_stat
    GROUP BY userId)

    """

    items = client.execute(sql)

    return items


def create_fishretail():
    """
    Получение с таблицы fishretail user_id, company_id

    return columns: user_id, fishretail_company_id
    """
    db = create_connect_db_m16_stage()
    cursor = db.cursor()

    sql = """
    SELECT user_id, company_id as fishretail_company_id
    FROM fishretail.user_profile
    WHERE company_id is not null
    """

    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    return data


def create_meat_info():
    """
    Получение с таблицы meatinfo user_id, company_id

    return columns: user_id, meatinfo_company_id
    """
    db = create_connect_db_m16_stage()
    cursor = db.cursor()

    sql = """
    SELECT user_id, company_id as meatinfo_company_id
    FROM meatinfo.user_profile
    WHERE company_id is not null
    """

    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    return data


def tradeboard():
    """
    Выгрузка полей itemId, userId, title, label, category_name, site, dateCreated из таблицы tradeboard

    return columns: itemId, userId, title, label, category_name, site, dateCreated
    """

    client = create_client_ch()

    sql = """
    SELECT itemId, userId, title, label, category_name, site, dateCreated
    FROM axe.tradeboard
    """
    items = client.execute(sql)

    return items


def user_profile():
    """
    Выгрузка полей  из таблицы user_profile

    return columns: userId, login, site
    """

    client = create_client_ch()

    sql = """
    SELECT userId, login, site
    FROM axe.userProfile
    """
    items = client.execute(sql)

    return items
