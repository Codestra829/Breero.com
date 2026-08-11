import hashlib

import redis.asyncio as redis
from fastapi import HTTPException, Request

from app.config import settings


def rate_limit(scope: str, requests: int, window_seconds: int):
    """Redis-backed fixed-window limit shared by every API process."""

    async def enforce(request: Request) -> None:
        source = request.client.host if request.client else "unknown"
        identity = hashlib.sha256(source.encode()).hexdigest()[:24]
        key = f"ratelimit:{scope}:{identity}"
        client = redis.from_url(settings.redis_url, socket_timeout=1)
        try:
            async with client.pipeline(transaction=True) as pipeline:
                pipeline.incr(key)
                pipeline.expire(key, window_seconds, nx=True)
                count, _ = await pipeline.execute()
        except redis.RedisError as exc:
            # Authentication/payment mutation limits fail closed. Readiness should
            # already have removed an instance whose Redis dependency is unhealthy.
            raise HTTPException(503, "rate limiter unavailable") from exc
        finally:
            await client.aclose()
        if int(count) > requests:
            raise HTTPException(429, "rate limit exceeded", headers={"Retry-After": str(window_seconds)})

    return enforce
