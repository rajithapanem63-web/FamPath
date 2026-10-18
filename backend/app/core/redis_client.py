"""
Redis client with in-memory fallback for local dev without Redis.
In production, set FAMPATH_REDIS_URL to a real Redis instance.
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from typing import Any

from app.core.config import get_settings

_settings = get_settings()

# ── In-memory fallback store ──────────────────────────────────────────────────
_memory_store: dict[str, Any] = {}
_memory_expiry: dict[str, float] = {}
_memory_zsets: dict[str, dict[str, float]] = defaultdict(dict)

_redis_available = False
_redis_client: Any = None


def _try_connect_redis() -> Any:
    """Try to connect to Redis; return client or None."""
    global _redis_available, _redis_client
    url = _settings.REDIS_URL
    # If REDIS_URL is localhost or empty, avoid hanging or failing on cloud without local redis
    if not url or "localhost" in url or "127.0.0.1" in url:
        _redis_available = False
        return None
    try:
        import redis.asyncio as aioredis  # type: ignore[import-untyped]
        pool = aioredis.ConnectionPool.from_url(
            url, max_connections=20, decode_responses=True, socket_timeout=1
        )
        client = aioredis.Redis(connection_pool=pool)
        _redis_client = client
        _redis_available = True
        return client
    except Exception:
        _redis_available = False
        return None


def get_redis() -> Any:
    """Return Redis client or in-memory stub."""
    if _redis_available and _redis_client:
        return _redis_client
    client = _try_connect_redis()
    if client:
        return client
    return _InMemoryRedis()


class _InMemoryRedis:
    """
    Minimal Redis-compatible in-memory stub.
    Used when Redis is not available (local dev without Docker).
    NOT suitable for production — no persistence, no cross-process sharing.
    """

    async def ping(self) -> bool:
        return True

    async def get(self, key: str) -> str | None:
        if key in _memory_expiry and time.time() > _memory_expiry[key]:
            _memory_store.pop(key, None)
            _memory_expiry.pop(key, None)
            return None
        return _memory_store.get(key)

    async def set(self, key: str, value: Any, ex: int | None = None) -> None:
        _memory_store[key] = value
        if ex:
            _memory_expiry[key] = time.time() + ex

    async def delete(self, *keys: str) -> None:
        for k in keys:
            _memory_store.pop(k, None)
            _memory_expiry.pop(k, None)

    async def expire(self, key: str, seconds: int) -> None:
        _memory_expiry[key] = time.time() + seconds

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> None:
        zset = _memory_zsets[key]
        to_remove = [m for m, s in zset.items() if min_score <= s <= max_score]
        for m in to_remove:
            del zset[m]

    async def zadd(self, key: str, mapping: dict[str, float]) -> None:
        _memory_zsets[key].update(mapping)

    async def zcard(self, key: str) -> int:
        return len(_memory_zsets[key])

    def pipeline(self) -> "_InMemoryPipeline":
        return _InMemoryPipeline(self)


class _InMemoryPipeline:
    def __init__(self, redis: _InMemoryRedis) -> None:
        self._redis = redis
        self._cmds: list[tuple[str, tuple[Any, ...]]] = []

    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> "_InMemoryPipeline":
        self._cmds.append(("zremrangebyscore", (key, min_score, max_score)))
        return self

    def zadd(self, key: str, mapping: dict[str, float]) -> "_InMemoryPipeline":
        self._cmds.append(("zadd", (key, mapping)))
        return self

    def zcard(self, key: str) -> "_InMemoryPipeline":
        self._cmds.append(("zcard", (key,)))
        return self

    def expire(self, key: str, seconds: int) -> "_InMemoryPipeline":
        self._cmds.append(("expire", (key, seconds)))
        return self

    async def execute(self) -> list[Any]:
        results = []
        for cmd, args in self._cmds:
            fn = getattr(self._redis, cmd)
            results.append(await fn(*args))
        return results


# ── Helpers ───────────────────────────────────────────────────────────────────

async def check_rate_limit(
    redis: Any,
    key: str,
    max_attempts: int,
    window_seconds: int,
) -> tuple[bool, int]:
    """Sliding-window rate limiter. Returns (allowed, remaining)."""
    now = time.time()
    window_start = now - window_seconds

    try:
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds)
        results = await pipe.execute()

        count: int = results[2]
        allowed = count <= max_attempts
        remaining = max(0, max_attempts - count)
        return allowed, remaining
    except Exception:
        # Fallback to in-memory store
        pipe = _InMemoryRedis().pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds)
        results = await pipe.execute()
        count = results[2]
        return count <= max_attempts, max(0, max_attempts - count)


async def cache_set(redis: Any, key: str, value: Any, ttl_seconds: int = 300) -> None:
    try:
        await redis.set(key, json.dumps(value), ex=ttl_seconds)
    except Exception:
        await _InMemoryRedis().set(key, json.dumps(value), ex=ttl_seconds)


async def cache_get(redis: Any, key: str) -> Any | None:
    try:
        raw = await redis.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception:
        raw = await _InMemoryRedis().get(key)
        return json.loads(raw) if raw is not None else None


async def cache_delete(redis: Any, key: str) -> None:
    try:
        await redis.delete(key)
    except Exception:
        await _InMemoryRedis().delete(key)
