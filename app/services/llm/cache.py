"""LLM 호출 결과용 경량 TTL 캐시 (gaeoanalysis `lib/llm/cache.ts` 포트)."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Dict, Generic, Optional, TypeVar

V = TypeVar("V")


class TTLCache(Generic[V]):
    def __init__(self, ttl_ms: int = 60 * 60 * 1000, max_entries: int = 500) -> None:
        self._ttl_ms = ttl_ms
        self._max_entries = max_entries
        self._store: Dict[str, tuple[V, float]] = {}

    def get(self, key: str) -> Optional[V]:
        hit = self._store.get(key)
        if hit is None:
            return None
        value, expires = hit
        if time.time() * 1000 > expires:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: V) -> None:
        if len(self._store) >= self._max_entries:
            oldest = next(iter(self._store))
            del self._store[oldest]
        self._store[key] = (value, time.time() * 1000 + self._ttl_ms)

    async def wrap(self, key: str, factory: Callable[[], Awaitable[V]]) -> V:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = await factory()
        self.set(key, value)
        return value


def hash_key(input_text: str) -> str:
    """캐시 키용 안정적 해시(djb2)."""
    h = 5381
    for ch in input_text:
        h = ((h * 33) ^ ord(ch)) & 0xFFFFFFFF
    return format(h, "x")
