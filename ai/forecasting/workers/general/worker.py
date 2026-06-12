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
        queues=['common models'],
        connection=redis,
        serializer=JSONSerializer
    )
    worker.work()


if __name__ == '__main__':
    processes = []
    for i in range(NUM_WORKERS):
        p = multiprocessing.Process(target=start_worker)
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
