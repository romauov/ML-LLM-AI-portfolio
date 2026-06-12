"""
запуск сервиса прогнозатора

@author Sergei Romanov
"""
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.predictor.predictor import predict_pipline
from config.configs import Config
from app.api.router import router
from app.common.logger import logger as log
from dashboards.grafana_dashboard import update_dashboard_for_accumulated_historical_data

cfg = Config.from_yaml_week()
cfg_month = Config.from_yaml_month()

MISFIRE_GRACE_TIME = 60 * 10


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом приложения FastAPI.

    Запускает и останавливает планировщик задач.

    :param app: Экземпляр приложения FastAPI.
    """
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        predict_pipline,
        CronTrigger(
            day_of_week=cfg.scheduler.forecasting.day_of_week,
            hour=cfg.scheduler.forecasting.hour,
            minute=cfg.scheduler.forecasting.minute,
            start_date=datetime.now()
        ),
        misfire_grace_time=MISFIRE_GRACE_TIME,
        kwargs={
            'cfg': cfg,
        }
    )

    # каждый месяц с первого по седьмой день в воскресенье в 21:00
    scheduler.add_job(
        predict_pipline,
        CronTrigger(
            day=cfg_month.scheduler.forecasting.day,
            hour=cfg_month.scheduler.forecasting.hour,
            minute=cfg_month.scheduler.forecasting.minute,
            day_of_week=cfg_month.scheduler.forecasting.day_of_week
        ),
        misfire_grace_time=MISFIRE_GRACE_TIME,
        kwargs={
            'cfg': cfg_month,
        }
    )

    # Добавляем задачу для выполнения задачи дашборда графаны
    scheduler.add_job(
        update_dashboard_for_accumulated_historical_data,
        CronTrigger(
            day_of_week=cfg.scheduler.dashboards.day_of_week,
            hour=cfg.scheduler.dashboards.hour,
            minute=cfg.scheduler.dashboards.minute,
            start_date=datetime.now()
        ),
        misfire_grace_time=MISFIRE_GRACE_TIME,
        kwargs={
            'cfg': cfg,
        }
    )

    # Запускаем планировщик
    scheduler.start()

    for job in scheduler.get_jobs():
        log.info(f"Name: {job.name}, Trigger: {job.trigger}, Next Run Time: {job.next_run_time}")

    # Возвращаем управление, позволяя приложению работать
    yield

    # Останавливаем планировщик при завершении работы приложения
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(router)
