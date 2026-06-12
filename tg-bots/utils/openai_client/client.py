"""
асинхронный клиент ChatGPT

@author Sergei Romanov
"""

import httpx
from openai import AsyncOpenAI
from utils.settings import secrets as s

client = AsyncOpenAI(
    base_url=s.openai.proxy,
    api_key=s.openai.key,
    http_client=httpx.AsyncClient(verify=False)
    )
