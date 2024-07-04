import json
from dataclasses import asdict, dataclass
from functools import wraps
from logging import getLogger
from typing import Any, Awaitable, Callable

from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from cachey.backends.utils import convert_func_name_and_args_to_str
from cachey.cache.base import CacheRegistry
from cachey.cleaners.cleaner import FunctionCleaner
from cachey.exceptions.base import CacheNotInitializedError, ResponseTypeNotSupported

logger = getLogger(__name__)


@dataclass
class CachedResponse:
    data: str | bytes | list | dict
    is_fastapi_response_subclass: bool
    fastapi_response_class: str | None
    raw_response_headers: list[tuple[bytes, bytes]] | None = None

    def set_headers(self, headers: list[tuple[bytes, bytes]]):
        self.raw_response_headers = headers


def encode(data: Any, headers=None) -> str:
    if isinstance(data, (dict, list, str)):
        returning_value = CachedResponse(data, False, None)
    elif isinstance(data, (JSONResponse, HTMLResponse, PlainTextResponse)):
        returning_value = CachedResponse(
            data.body.decode(), True, data.__class__.__name__
        )
    elif isinstance(data, bytes):
        returning_value = CachedResponse(data.decode(), False, None)
    else:
        raise ResponseTypeNotSupported(
            """
    type of response is not supported.
    Supported types: dict, list, bytes, FastAPI's Response
    """
        )
    if headers:
        headers = [
            (k.lower().decode("latin-1"), v.decode("latin-1")) for k, v in headers
        ]
        returning_value.set_headers(headers)
    return json.dumps(asdict(returning_value))


def decode(
    data: str,
) -> HTMLResponse | JSONResponse | PlainTextResponse | dict | list | str | bytes:
    data_dict = json.loads(data)
    cached_response = CachedResponse(**data_dict)
    if cached_response.is_fastapi_response_subclass:
        match cached_response.fastapi_response_class:
            case "HTMLResponse":
                return HTMLResponse(cached_response.data)
            case "JSONResponse":
                return JSONResponse(cached_response.data)
            case "PlainTextResponse":
                return PlainTextResponse(cached_response.data)
    if data_dict["raw_response_headers"]:
        data_dict["raw_response_headers"] = [
            (k.lower().encode("latin-1"), v.encode("latin-1"))
            for k, v in data_dict["raw_response_headers"]
        ]
    return data_dict


def cache(
    *,
    ttl: int = 60,
):
    def wrapper(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def inner(*args, **kwargs) -> Any:
            registry = CacheRegistry.get_instance()
            if not registry:
                raise CacheNotInitializedError(
                    "cache is not initialized and backend is not provided"
                )
            logger.info("aba aba")
            cleaner = FunctionCleaner(func, kwargs)
            kwargs_without_deps = cleaner.get_kwargs_without_injected_deps()
            kwargs_with_deps = cleaner.get_kwargs_with_injected_deps()
            key = convert_func_name_and_args_to_str(
                "app_cache", func, **kwargs_without_deps
            )
            cached = await registry.get_cached(key)
            if cached is not None:
                cached_dict = decode(cached)
                if cached_dict and cached_dict["raw_response_headers"]:  # type: ignore
                    response = cleaner.get_response()
                    response.raw_headers.extend(cached_dict["raw_response_headers"])  # type: ignore
            else:
                cached = await func(*args, **kwargs_with_deps)
                response = cleaner.get_response()
                if response:
                    headers = cleaner.get_response_raw_headers()
                    response.raw_headers = headers
                cached = encode(cached, headers)
                await registry.set_key(key, cached, ttl)
            return decode(cached)

        return inner

    return wrapper
