import json

from rq.job import Dependency, get_current_job, Job

from app.redis_queue.connect import JOB_EXECUTION_TIMEOUT, RESUL_TTL, JOB_QUEUE_TTL, REDIS_CONN, SERIALIZER
from app.redis_queue.queues import Q_CUDA_ARIMA, Q_COMMON_MODELS, Q_CUDA_NEURALPROPHET, Q_COMMON_TASKS, Q_CUDA_TIMESFM
from app.common.logger import logger as log


def set_predict_arima_task(df, cfg, forecasting_date=None):
    log.info('add job to arima prediction')

    return Q_CUDA_ARIMA.enqueue_call(
        func='app.predict.predict_with_hyperparameter_tuning',
        args=(df.to_json(force_ascii=False), cfg.dict(), forecasting_date),
        kwargs={},
        timeout=JOB_EXECUTION_TIMEOUT,
        result_ttl=RESUL_TTL,
        ttl=JOB_QUEUE_TTL
    )


def set_predict_es_task(df, cfg, forecasting_date=None):
    log.info('add job to Exponential smoothing prediction')

    return Q_COMMON_MODELS.enqueue_call(
        func='app.predict.predict_with_hyperparameter_tuning',
        args=(df.to_json(force_ascii=False), cfg.dict(), forecasting_date, 'Exponential smoothing'),
        kwargs={},
        timeout=JOB_EXECUTION_TIMEOUT,
        result_ttl=RESUL_TTL,
        ttl=JOB_QUEUE_TTL
    )


def set_predict_prophet_task(df, cfg, forecasting_date=None):
    log.info('add job to Prophet prediction')

    return Q_COMMON_MODELS.enqueue_call(
        func='app.predict.predict_with_hyperparameter_tuning',
        args=(df.to_json(force_ascii=False), cfg.dict(), forecasting_date, 'Prophet'),
        kwargs={},
        timeout=JOB_EXECUTION_TIMEOUT,
        result_ttl=RESUL_TTL,
        ttl=JOB_QUEUE_TTL
    )


def set_predict_theta_task(df, cfg, forecasting_date=None):
    log.info('add job to ThetaModel prediction')

    return Q_COMMON_MODELS.enqueue_call(
        func='app.predict.predict_with_hyperparameter_tuning',
        args=(df.to_json(force_ascii=False), cfg.dict(), forecasting_date, 'ThetaModel'),
        kwargs={},
        timeout=JOB_EXECUTION_TIMEOUT,
        result_ttl=RESUL_TTL,
        ttl=JOB_QUEUE_TTL
    )


def set_predict_neuralprophet_task(df, cfg, forecasting_date=None):
    log.info('add job to NeuralProphet prediction')

    return Q_CUDA_NEURALPROPHET.enqueue_call(
        func='app.predict.predict_with_hyperparameter_tuning',
        args=(df.to_json(force_ascii=False), cfg.dict(), forecasting_date),
        kwargs={},
        timeout=JOB_EXECUTION_TIMEOUT,
        result_ttl=RESUL_TTL,
        ttl=JOB_QUEUE_TTL
    )


def set_predict_timesfm_task(df, cfg, forecasting_date=None):
    log.info('add job to TimesFM prediction')

    return Q_CUDA_TIMESFM.enqueue_call(
        func='app.predict.predict_with_hyperparameter_tuning',
        args=(df.to_json(force_ascii=False), cfg.dict(), forecasting_date),
        kwargs={},
        timeout=JOB_EXECUTION_TIMEOUT,
        result_ttl=RESUL_TTL,
        ttl=JOB_QUEUE_TTL
    )


def set_save_result_task(depends_on: Dependency):
    return Q_COMMON_TASKS.enqueue_call(
        func='app.database.tasks.save_predictions',
        args=(), kwargs={}, depends_on=depends_on
    )


def _collect_group_result():
    result = []
    for dependency_job_id in get_current_job().dependency_ids:
        job = Job.fetch(dependency_job_id, connection=REDIS_CONN, serializer=SERIALIZER)
        predictions = job.return_value()
        if predictions:
            result.append(json.loads(predictions)['result'])
        else:
            log.info(f'this job has no result {job}')
    return json.dumps({"result": result})


def set_return_grouping_tasks_result(depends_on: Dependency):
    return Q_COMMON_TASKS.enqueue_call(
        func=_collect_group_result,
        args=(), kwargs={}, depends_on=depends_on
    )
