"""
Функции для работы с базой данных.

@author Nikolay Zhabchikov
"""
import time

from sqlalchemy.exc import DisconnectionError, OperationalError
from sqlalchemy import create_engine, text
import pandas as pd

from app.common.constants import INDICATORS_COUNT_COL, INDICATORS_DATE_COL, AGRO_PERIOD_COL, \
    AGRO_FARMS_CATEGORY_COL, AGRO_REGION_COL, AGRO_CATEGORY_COL, AGRO_FARMS_OF_ALL_CATEGORY, \
    AGRO_REGION_RUSSIAN_FEDERATION
from app.common.enums import ProductsType
from app.common.settings import secrets as s
from app.common.logger import logger as log
from app.database.utils import make_sql_request_from_table_metadata, get_seafood_table_and_columns_by_type

db_user = s.db_user
db_password = s.db_password
db_host = s.db_host
db_port = s.db_port
db_name = s.db_name
db_raw_meat_table_name = s.db_table_raw_meat
db_forecasting_history_table_name = s.db_table_forecasting_history
db_predicted_price_table_name = s.db_table_predicted_price

engine = create_engine(f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}', pool_pre_ping=True)

FREQUENCY_PANDAS_TO_DB_MAPPING = {
    'W-MON': 'week',
    "MS": "month",
}


def safety_db_connect(retries=5, delay=60):
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0

            while attempt < retries:
                db_connect = engine.connect()
                try:
                    result = func(db_connect=db_connect, *args, **kwargs)
                    return result

                except (OperationalError, DisconnectionError) as e:
                    db_connect.rollback()
                    log.error(f"Database error in {func.__name__}: {str(e)}")
                    attempt += 1
                    if attempt < retries:
                        # Экспоненциальная задержка
                        time.sleep(delay * attempt)

                except Exception as e:
                    db_connect.rollback()
                    log.error(f"General error in {func.__name__}: {str(e)}")
                    attempt += 1
                    if attempt < retries:
                        time.sleep(delay)

                finally:
                    db_connect.close()

            raise RuntimeError(f"Function {func.__name__} failed after {retries} attempts")

        return wrapper

    return decorator


@safety_db_connect()
def get_seafood_data(products_type: ProductsType, sql_condition, date_from, date_to, db_connect):
    table, columns = get_seafood_table_and_columns_by_type(products_type)

    request = f'''
        SELECT id, date, price, product, federal_okrug, {columns}
        FROM {table}
        WHERE 
            date >= '{date_from}' AND date <= '{date_to}'
            AND {sql_condition}
            AND is_outlier = False
        '''

    df = pd.read_sql(request, db_connect, index_col='id')

    return df


@safety_db_connect()
def get_meat_data(sql_condition, date_from, date_to, db_connect):
    """
    Получение данных с мясных мониторингов.
    :param sql_condition: Условие в SQL запросе без "where"
    :param db_connect: подключение к базе данных.
    :param date_to: Дата конца выгрузки данных.
    :param date_from: Дата начала выгрузки данных.
    :return: dataframe.
    """
    request = f'''
        SELECT 
            id, 
            product, 
            product_type, 
            date, 
            price, 
            federal_okrug, 
            sort,
            certification, 
            temperature_state, 
            product_details
        FROM {db_raw_meat_table_name}
        WHERE 
            date >= '{date_from}' AND date <= '{date_to}'
            AND {sql_condition}
            AND is_outlier = False
        '''
    df = pd.read_sql(request, db_connect, index_col='id')

    return df


def save_forecasting(df):
    """
    Сохранение предсказаний в базу данных.
    :param df: dataframe с предсказаниями.
    :return:
    """
    log.info('start saving predictions to database')
    df_history = _save_forecasting_history(df)
    df = pd.merge(df, df_history, how='left', on=['ID', 'model'])
    df = df.explode(['dates', 'preds']).reset_index(drop=True)
    _save_predicted_prices(df)
    log.info('end saving predictions')


@safety_db_connect()
def _save_forecasting_history(df, db_connect):
    """
    Сохранение мета информации предсказывающих моделей.
    :param df: dataframe с предсказаниями.
    :return: dataframe, сохраненная мета информация.
    """
    current_date = df['forecasting_date'].values[0]

    values = [
        (
            f"('{row['forecasting_date']}', "
            f"'{row['model']}', "
            f"{row['forecast_horizon']}, "
            f"'1 {FREQUENCY_PANDAS_TO_DB_MAPPING.get(row['frequency'])}', "
            f"0, "
            f"{round(row['mape'], 2)}, "
            f"'{row['ID']}')"
        )
        for _, row in df.iterrows()
    ]
    request = f'''
        INSERT INTO {db_forecasting_history_table_name} 
            (date, model, forecast_horizon, frequency, best_model, mape_at_test, time_series_id)
        VALUES {', '.join(values)}
    '''
    db_connect.execute(text(request))
    db_connect.commit()

    request = f'''
        SELECT id, model, time_series_id as ID
        FROM {db_forecasting_history_table_name}
        WHERE date = '{current_date}'
    '''
    df = pd.read_sql(request, db_connect)

    return df


@safety_db_connect()
def _save_predicted_prices(df, db_connect):
    """
    Сохранение непосредственных предсказаний.
    :param df: dataframe с предсказаниями и мета информацией моделей.
    :return:
    """
    values = []
    for _, row in df.iterrows():
        row = row.to_dict()
        values.append(f"('{row['dates']}', {row['preds']}, {row['id']})")
    values_str = ', '.join(values)
    request = f'''
        INSERT INTO {db_predicted_price_table_name} 
            (date, price, forecasting_id)
        VALUES {values_str}
    '''
    db_connect.execute(text(request))
    db_connect.commit()


@safety_db_connect()
def _get_indicators_table_metadata(tables_title, db_connect):
    """
    Получение информации о структуре таблиц индикаторов.
    :param tables_title: Названия таблиц.
    :return: dataframe.
    """
    indicators_str = str(tuple(tables_title))
    if len(tables_title) == 1:
        indicators_str = indicators_str.replace(',', '')

    metadata_df = pd.read_sql(
        f"""
            with ind as (
                select id, title from indicator
                where title in {indicators_str}
            )

            select ic.id, ic.name, ic.position, ic.indicator_id, ind.title from indicator_column ic
            inner join ind on ind.id=ic.indicator_id
        """,
        db_connect,
    )
    metadata_df.columns = metadata_df.columns.str.replace('_', ' ')
    return metadata_df


@safety_db_connect()
def get_macroeconomic_indicators(cfg, db_connect):
    """
    Получение датафрейма с макроэкономическими показателями.
    :return: dataframe.
    """
    metadata_df = _get_indicators_table_metadata(cfg.macroeconomic_indicators)

    economic_indicators = None
    for i, indicator_id in enumerate(metadata_df['indicator id'].unique()):
        df = metadata_df[metadata_df['indicator id'] == indicator_id]
        title = df['title'].unique()[0]
        request = make_sql_request_from_table_metadata(df, indicator_id)

        df = pd.read_sql(request, db_connect)
        df = df.rename(columns={INDICATORS_COUNT_COL: title, INDICATORS_DATE_COL: 'ds'})

        if i == 0:
            economic_indicators = df
        else:
            economic_indicators = pd.merge(economic_indicators, df, on=['ds'], how='outer', suffixes=('', '_drop'))

    economic_indicators = economic_indicators.drop(economic_indicators.filter(regex='_drop$').columns, axis=1)
    economic_indicators['ds'] = pd.to_datetime(economic_indicators['ds'])
    return economic_indicators


@safety_db_connect()
def get_agro_indicators(cfg, db_connect):
    """
    Получение датафрейма с аграрными показателями.
    :return: dataframe.
    """
    metadata_df = _get_indicators_table_metadata(cfg.agro_indicators)

    agro_indicators = None
    for i, indicator_id in enumerate(metadata_df['indicator id'].unique()):
        df = metadata_df[metadata_df['indicator id'] == indicator_id]
        title = df['title'].unique()[0]
        request = make_sql_request_from_table_metadata(df, indicator_id)

        df = pd.read_sql(request, db_connect)
        df = df.rename(columns={INDICATORS_COUNT_COL: title, INDICATORS_DATE_COL: 'ds'})

        if AGRO_PERIOD_COL in df.columns:
            df = df.drop(df[df[AGRO_PERIOD_COL].str.contains('-')].index)

        if AGRO_FARMS_CATEGORY_COL in df.columns:
            df = df[df[AGRO_FARMS_CATEGORY_COL].str.lower().str.strip().str.contains(AGRO_FARMS_OF_ALL_CATEGORY)]

        df = df[df[AGRO_REGION_COL].str.lower().str.strip().str.contains(AGRO_REGION_RUSSIAN_FEDERATION)]

        if AGRO_CATEGORY_COL in df.columns:
            df = df.pivot_table(index='ds', columns=AGRO_CATEGORY_COL, values=title)
            df = df[df.columns.intersection(cfg.agro_indicators_product_categories)]
            df = df.add_suffix(f'_{title}')
            df = df.reset_index()
        else:
            df = df[['ds', title]]

        if i == 0:
            agro_indicators = df
        else:
            agro_indicators = pd.merge(agro_indicators, df, on=['ds'], how='outer', suffixes=('', '_drop'))

    agro_indicators = agro_indicators.drop_duplicates('ds', ignore_index=True)
    agro_indicators = agro_indicators.drop(agro_indicators.filter(regex='_drop$').columns, axis=1)
    agro_indicators['ds'] = pd.to_datetime(agro_indicators['ds'])
    return agro_indicators


@safety_db_connect()
def get_predictions_by_date(date, db_connect):
    df_predictions = pd.read_sql(
        f"""
            WITH fh AS (
                SELECT 
                    id,
                    date,
                    time_series_id,
                    model
                FROM forecasting_history
                WHERE date = '{date}'
            )
            SELECT 
                pp.id, 
                fh.time_series_id,
                pp.date,
                fh.model,
                pp.price
            FROM predicted_prices pp
            JOIN fh on fh.id = pp.forecasting_id
        """,
        db_connect,
        index_col='id'
    )
    return df_predictions


@safety_db_connect()
def save_grafana_dashboard_mape_metrics(df, db_connect):
    """
    Сохранение метрик ошибки предсказаний в для графаны.
    :param df: dataframe с метриками.
    :return:
    """
    values = []
    for _, row in df.iterrows():
        row = row.to_dict()
        values.append(f"('{row['date']}', '{row['ID']}', '{row['model']}', {row['mape']})")
    values_str = ', '.join(values)
    request = f'''
        INSERT INTO dashboard_grafana_forecasting_mape 
            (date, time_series_id, model, mape)
        VALUES {values_str}
    '''
    db_connect.execute(text(request))
    db_connect.commit()


@safety_db_connect()
def get_forecasting_dates_with_enough_data_for_metrics(freq, n_forecasts, db_connect):
    request = f"""
        SELECT 
            DISTINCT fh.date
        FROM forecasting_history fh
        WHERE fh.frequency = '1 {FREQUENCY_PANDAS_TO_DB_MAPPING.get(freq)}'
            AND fh.date <= DATE_SUB(CURDATE(), INTERVAL {n_forecasts} {FREQUENCY_PANDAS_TO_DB_MAPPING.get(freq)})
            AND fh.date > (
                SELECT 
                COALESCE(MAX(date), '2025-10-26 00:00:00')
                FROM dashboard_grafana_forecasting_mape
            )
        ORDER BY fh.date ASC
        LIMIT 10
    """
    result = db_connect.execute(text(request))
    return [r.date for r in result]
