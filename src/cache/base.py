from typing import Any, Self

from src.backends.base import AbstractBackend
from src.exceptions.base import CannotInitCacheTwice


class CacheRegistry:
    _instance = None

    __slots__ = "backend"

    def __new__(cls, *args, **kwargs) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> None | Self:
        return cls._instance

    def __init__(self, backend: AbstractBackend) -> None:
        if hasattr(self, "backend"):
            raise CannotInitCacheTwice("cannot initialize cache twice")
        else:
            self.backend = backend

    async def set_key(self, key: str, value: Any, ttl: int) -> None:
        await self.backend.set(key, value, ttl)

    async def get_cached(self, key: str) -> Any:
        return await self.backend.get(key)
