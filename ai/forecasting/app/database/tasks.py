import json

import pandas as pd
from rq import get_current_job
from rq.job import Job

from app.database.db import save_forecasting
from app.redis_queue.connect import REDIS_CONN, SERIALIZER
from app.common.logger import logger as log


def save_predictions():
    for job_id in get_current_job().dependency_ids:
        job = Job.fetch(job_id, connection=REDIS_CONN, serializer=SERIALIZER)
        predictions = job.return_value()
        df = pd.DataFrame(json.loads(predictions)['result'])
        if predictions:
            log.info(f'save predictions from {job.worker_name}')
            save_forecasting(df)
