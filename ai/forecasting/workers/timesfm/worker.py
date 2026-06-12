"""
Запуск RQ-воркера для очереди TimesFM.

@author Dmitry Avzalov
"""

import multiprocessing
import os

from redis import Redis, ConnectionPool
from rq import Worker
from rq.serializers import JSONSerializer

REDIS_PORT = int(os.getenv('REDIS_PORT'))
NUM_WORKERS = int(os.getenv('NUM_WORKERS'))


def start_worker():
    pool = ConnectionPool(
        host='redis',
        port=REDIS_PORT,
        socket_connect_timeout=None,
        socket_timeout=None,
        socket_keepalive=True,
        retry_on_timeout=True,
        health_check_interval=30
    )
    redis = Redis(connection_pool=pool)
    worker = Worker(
        queues=['cuda timesfm'],
        connection=redis,
        serializer=JSONSerializer
    )
    worker.work()


if __name__ == '__main__':
    processes = []
    for _ in range(NUM_WORKERS):
        process = multiprocessing.Process(target=start_worker)
        process.start()
        processes.append(process)

    for process in processes:
        process.join()
