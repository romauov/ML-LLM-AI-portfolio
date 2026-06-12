from rq import Worker
from redis import Redis, ConnectionPool
from rq.serializers import JSONSerializer

pool = ConnectionPool(
    host='redis',
    port=6379,
    socket_connect_timeout=None,
    socket_timeout=None,
    socket_keepalive=True,
    retry_on_timeout=True
)
REDIS_CONN = Redis(connection_pool=pool)
SERIALIZER = JSONSerializer
WORKER = Worker

SECOND = 1
MINUTE = SECOND * 60
HOUR = MINUTE * 60

CALLBACK_TIMEOUT = MINUTE * 5
RESUL_TTL = MINUTE * 10
JOB_QUEUE_TTL = HOUR * 12
JOB_EXECUTION_TIMEOUT = HOUR * 24
