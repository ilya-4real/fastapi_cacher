from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(eq=False)
class AbstractBackend(ABC):
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> None:
        raise NotImplementedError
