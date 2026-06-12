"""
Модуль предсказания.

@author Nikolay Zhabchikov
"""
from datetime import datetime, timedelta

from rq.job import Dependency

from app.data.handlers.from_database import get_data_from_database
from app.common.logger import logger as log
from app.data.utils import add_global_indicators
from app.redis_queue.queue_tasks import set_predict_arima_task, set_predict_es_task, set_predict_prophet_task, \
    set_predict_theta_task, set_predict_neuralprophet_task, set_predict_timesfm_task, set_save_result_task


def predict_pipline(cfg, date_from=None, date_to=None):
    """
    Пайплайн прогнозирования временного ряда.
    :param cfg: Config.
    :param date_from: дата начала выборки.
    :param date_to: дата конца выборки.
    """
    if not date_from:
        date_from = (datetime.today() - timedelta(days=365 * cfg.years_of_historical_data)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.today().strftime('%Y-%m-%d')

    df = get_data_from_database(date_from=date_from, date_to=date_to, cfg=cfg, for_dashboard=False)

    log.info('added task to queues')
    forecasting_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

    job_arima = set_predict_arima_task(df, cfg, forecasting_date)
    set_save_result_task(Dependency(jobs=[job_arima]))

    job_common_es = set_predict_es_task(df, cfg, forecasting_date)
    set_save_result_task(Dependency(jobs=[job_common_es]))

    job_common_prophet = set_predict_prophet_task(df, cfg, forecasting_date)
    set_save_result_task(Dependency(jobs=[job_common_prophet]))

    job_common_theta = set_predict_theta_task(df, cfg, forecasting_date)
    set_save_result_task(Dependency(jobs=[job_common_theta]))

    if not cfg.use_only_light_models:
        job_timesfm = set_predict_timesfm_task(df, cfg, forecasting_date)
        set_save_result_task(Dependency(jobs=[job_timesfm]))

        df_extend = add_global_indicators(df, cfg=cfg)
        job_neuralprophet = set_predict_neuralprophet_task(df_extend, cfg, forecasting_date)
        set_save_result_task(Dependency(jobs=[job_neuralprophet]))
    log.info('all task successful stored')
