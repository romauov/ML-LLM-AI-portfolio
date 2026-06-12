from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.router import router
from api.userdata import update_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        update_cache,
        CronTrigger(
            day_of_week="sat",
            hour=21,
            minute=0,
            start_date=datetime.now()
        )
    )

    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(router)
