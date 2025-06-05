import redis.asyncio as redis
from typing import AsyncGenerator
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield r
    finally:
        await r.close() 