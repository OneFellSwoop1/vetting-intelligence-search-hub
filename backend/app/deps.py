import redis.asyncio as redis
from typing import AsyncGenerator, Optional
import os

REDIS_URL = os.getenv("REDIS_URL", "").strip()

async def get_redis() -> AsyncGenerator[Optional[redis.Redis], None]:
    """Yield an async Redis client, or None if REDIS_URL is not configured."""
    if not REDIS_URL:
        yield None
        return
    r = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        yield r
    finally:
        await r.close() 