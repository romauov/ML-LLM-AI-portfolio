"""
роутер Fast API

@author Sergei Romanov
"""
import json
import os
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from rq.job import Dependency, JobStatus

from app.common.enums import DateFrequency
from app.data.checker import DataChecker
from app.common.settings import secrets as s
from app.data.handlers.main import get_data_by_config
from app.redis_queue.queue_tasks import set_predict_arima_task, set_predict_es_task, set_predict_prophet_task, \
    set_predict_theta_task, set_predict_neuralprophet_task, set_predict_timesfm_task, set_return_grouping_tasks_result
from app.redis_queue.queues import Q_COMMON_TASKS
from config.update_utils import prepare_prediction_config

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
data_dir = os.path.join(project_root, 'storage')
os.makedirs(data_dir, exist_ok=True)

router = APIRouter()
security = HTTPBasic()


def authentication(creds: HTTPBasicCredentials = Depends(security)):
    """
    Проверка аутентификации пользователя.

    :param creds: Учетные данные пользователя (имя пользователя и пароль).
    :raises HTTPException: Если имя пользователя или пароль неверны.
    """
    if not (creds.username == s.api_user and creds.password == s.api_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль.",
            headers={"WWW-Authenticate": "Basic"},
        )


@router.post("/predict", dependencies=[Depends(authentication)])
async def start_prediction(
        file: UploadFile = File(...),
        sheet_name: str = Form(...),
        date_name: str = Form(...),
        series_name: str = Form(...),
        forecasting_steps: int = Form(gt=0),
        year_limit: Annotated[int, Form(gt=0)] = None,
        train_n_epochs: Annotated[int, Form(gt=0)] = None,
        use_only_light_models: bool = Form(default=True),
        data_frequency: DateFrequency = Form(...),
        sesoanal_period: int = Form(gt=0),
):
    """
    Запуск предсказания на основе загруженного файла Excel.

    :param file: Загружаемый файл Excel.
    :param sheet_name: Имя листа в Excel, содержащего данные.
    :param date_name: Название столбца с датами.
    :param series_name: Название столбца с временными рядами.
    :param forecasting_steps: Количество шагов для предсказания.
    :param use_only_light_models: Флаг использования только легких моделей. Исключается NeuralProphet.
    :param year_limit: Ограничение по годам для анализа данных (необязательный параметр).
    :param train_n_epochs: Количество эпох обучения neuralprophet, если не указан, то количество эпох будет зависеть от
     размера временного ряда, чем больше эпох, тем дольше обучение (необязательный параметр).
    :param data_frequency: Частотность данных
    :param sesoanal_period: Длина сезонного периода
    :raises HTTPException: Если файл не является Excel или если данные некорректны.
    :return: ID задачи предсказания.
    """
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400, detail="Допустимы только файлы .xlsx или .xls")

    excel_file = BytesIO(await file.read())

    # подготавливаем конфиг пайплайна предикции
    cfg = prepare_prediction_config(
        data_frequency=data_frequency,
        use_only_light_models=use_only_light_models,
        forecasting_steps=forecasting_steps,
        train_n_epochs=train_n_epochs,
        sesoanal_period=sesoanal_period
    )

    # проверка состояния данных
    DataChecker(cfg).check_data_from_excel(excel_file, sheet_name, date_name, series_name, year_limit)

    data = {
        'file_path': excel_file,
        'sheet_name': sheet_name,
        'date': date_name,
        'series': series_name,
        'year_limit': year_limit
    }

    df = get_data_by_config(cfg=cfg, file_data=data, for_dashboard=False)

    jobs = [
        set_predict_arima_task(df, cfg),
        set_predict_es_task(df, cfg),
        set_predict_prophet_task(df, cfg),
        set_predict_theta_task(df, cfg)
    ]
    if not use_only_light_models:
        jobs.append(set_predict_neuralprophet_task(df, cfg))
        jobs.append(set_predict_timesfm_task(df, cfg))

    job_group_results = set_return_grouping_tasks_result(
        depends_on=Dependency(
            jobs=jobs,
            allow_failure=True
        )
    )
    return {"task_id": job_group_results.id}


@router.get("/status/{task_id}", dependencies=[Depends(authentication)])
async def get_status(task_id: str):
    """
    Получение статуса задачи предсказания.

    :param task_id: ID задачи, статус которой нужно получить.
    :return: Статус задачи.
    """

    job = Q_COMMON_TASKS.fetch_job(task_id)
    if not job:
        return {"status": 'NotFound'}

    job_status = job.get_status()
    match job_status:
        case JobStatus.FINISHED | JobStatus.FAILED | JobStatus.CANCELED:
            return {"status": job_status}
        case _:
            return {"status": JobStatus.STARTED}


@router.get("/result/{task_id}", dependencies=[Depends(authentication)])
async def get_result(task_id: str):
    """
    Получение результата задачи предсказания.

    :param task_id: ID задачи, результат которой нужно получить.
    :return: Результат задачи, если она завершена, или статус "pending".
    """
    job = Q_COMMON_TASKS.fetch_job(task_id)
    if not job:
        return {"status": 'NotFound'}

    job_status = job.get_status()
    match job_status:
        case JobStatus.FINISHED:
            return json.loads(job.return_value())['result']
        case JobStatus.FAILED | JobStatus.CANCELED:
            return {"status": job_status}
        case _:
            return {"status": JobStatus.STARTED}
