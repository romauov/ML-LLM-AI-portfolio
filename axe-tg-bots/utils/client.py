import httpx
from openai import AsyncOpenAI
from utils.settings import secrets as s

client = AsyncOpenAI(
    base_url=s.openai_proxy,
    api_key=s.openai_key,
    http_client=httpx.AsyncClient(verify=False)
    )
