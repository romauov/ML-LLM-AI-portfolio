"""
запрос к ai.m16 для получения дополнительной информации о пользователях

@author Sergei Romanov
"""
import json
from pathlib import Path
import aiofiles
import asyncio
import httpx
from httpx import BasicAuth, ReadTimeout
from api.logger import logger as log
from settings import secrets as s

CACHE_PATH = Path('user_cache.json')
MAX_RETRIES = 3

async def fetch_user_data(site, user_id, skip_cache=False):
    if not skip_cache:
        cache = await read_cache()
        cache_key = f"{site}_{user_id}"
        if cache_key in cache:
            return cache[cache_key]

    url = s.ai_m16_url
    data = {"site": site, "userid": user_id}
    headers = {"Content-Type": "application/json"}
    auth = BasicAuth(s.ai_m16_user, s.ai_m16_password)

    async with httpx.AsyncClient() as client:
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.post(url, json=data, headers=headers, auth=auth)
                if response.status_code == 200:
                    user_details = json.loads(response.json().get('user_details', '{}'))
                    cache = await read_cache()
                    cache[f"{site}_{user_id}"] = user_details
                    await write_cache(cache)
                    return user_details
                else:
                    raise Exception(f"HTTP error: {response.status_code}")
            except ReadTimeout:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(1)
                    continue
                raise Exception(f"Timeout after {MAX_RETRIES} attempts")

async def update_cache():
    original_cache = await read_cache()
    updated_cache = {}

    for cache_key in original_cache:
        try:

            site, user_id = cache_key.split('_', 1)

            user_data = await fetch_user_data(site, user_id, skip_cache=True)
            updated_cache[cache_key] = user_data
        except ValueError:
            log.error(f"Invalid cache key format: {cache_key}")
            updated_cache[cache_key] = original_cache[cache_key]
        except Exception as e:
            log.error(f"Failed to update {cache_key}: {str(e)}")

            updated_cache[cache_key] = original_cache[cache_key]

    await write_cache(updated_cache)
    log.info('userdata updated')

async def read_cache():
    if not CACHE_PATH.exists():
        return {}
    try:
        async with aiofiles.open(CACHE_PATH, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content) if content else {}
    except (json.JSONDecodeError, Exception) as e:
        log.error(f"Ошибка чтения кэша: {str(e)}")
        return {}

async def write_cache(cache):
    async with aiofiles.open(CACHE_PATH, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(cache, indent=2, ensure_ascii=False))
