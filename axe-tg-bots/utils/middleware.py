import asyncio
from collections import defaultdict
import time
from aiogram.types import Message
from aiogram import BaseMiddleware


class UserThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit: float = 2.0):
        self.limit = limit
        self.user_last_request = defaultdict(float)
        super().__init__()

    async def __call__(self, handler, event: Message, data):
        user_id = event.from_user.id
        current_time = time.monotonic()
        last_request_time = self.user_last_request[user_id]
        elapsed = current_time - last_request_time

        if elapsed < self.limit:
            wait_time = self.limit - elapsed
            await asyncio.sleep(wait_time)
            current_time = time.monotonic()

        self.user_last_request[user_id] = current_time
        return await handler(event, data)
