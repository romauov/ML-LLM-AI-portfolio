import multiprocessing
import os

from redis import Redis
from rq import Worker
from rq.serializers import JSONSerializer

REDIS_PORT = int(os.getenv('REDIS_PORT'))
NUM_WORKERS = int(os.getenv('NUM_WORKERS'))


def start_worker():
    redis = Redis(host="redis", port=REDIS_PORT)
    worker = Worker(
        queues=['cuda neuralprophet'],
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
