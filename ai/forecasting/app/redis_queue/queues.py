from rq import Queue

from app.redis_queue.connect import REDIS_CONN, SERIALIZER

Q_CUDA_ARIMA = Queue(name='cuda arima', connection=REDIS_CONN, serializer=SERIALIZER)
Q_CUDA_NEURALPROPHET = Queue(name='cuda neuralprophet', connection=REDIS_CONN, serializer=SERIALIZER)
Q_CUDA_TIMESFM = Queue(name='cuda timesfm', connection=REDIS_CONN, serializer=SERIALIZER)
Q_COMMON_MODELS = Queue(name='common models', connection=REDIS_CONN, serializer=SERIALIZER)
Q_COMMON_TASKS = Queue(name='common tasks', connection=REDIS_CONN, serializer=SERIALIZER)
