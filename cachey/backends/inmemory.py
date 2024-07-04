from dataclasses import dataclass, field
from typing import Any

from cachey.backends.base import AbstractBackend
from cachey.exceptions.base import KeyNotFoundError

DEFAULT_TTL = 60


@dataclass(eq=False)
class InMemoryCacheBackend(AbstractBackend):
    cache_map: dict[str, tuple[float, Any]] = field(default_factory=dict)
    """Cache backend that lives in directly in memory
      and doesn't call any external service
    """

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """puts provided value to the cache. Value will be available to get by key

        Args:
            key (str): unique identifier of value
            value (Any): value to keep under the key
            ttl (int | None, optional): time to live for value.
            Value will not be deleted automatically.
            It will be deleted if it is requested.
            Defaults to None.
        """
        if not ttl:
            ttl = DEFAULT_TTL
        self.cache_map[key] = (ttl, value)

    async def get(self, key: str) -> Any | None:
        """tries to find cached value by key.
        returns it if found, else returns None

        Args:
            key (str): identifier of cached value

        Returns:
            Any | None: found cached value or None
        """
        try:
            return self.cache_map[key][1]
        except KeyError:
            return None

    async def delete(self, key: str) -> None:
        """deletes cached value

        Args:
            key (str): identifier of cached value
        """
        del self.cache_map[key]
