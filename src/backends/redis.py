from dataclasses import dataclass, field
from typing import Any

import redis.asyncio as redis

from src.backends.base import AbstractBackend


@dataclass(eq=False)
class RedisBackend(AbstractBackend):
    host: str
    port: int
    client: redis.Redis = field(init=False)

    def __post_init__(self):
        self.client = redis.Redis(host=self.host, port=self.port)

    async def set(self, key: str, value: Any, ttl: int) -> None:
        await self.client.set(key, value, ttl)

    async def get(self, key: str) -> Any:
        return await self.client.get(key)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)
