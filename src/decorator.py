import json
from dataclasses import asdict, dataclass
from functools import wraps
from inspect import Signature, signature
from typing import Awaitable, Callable, TypeVar

from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from src.backends.utils import convert_func_name_and_args_to_str
from src.cache.base import CacheRegistry
from src.cleaners.cleaner import FunctionCleaner
from src.exceptions.base import CacheNotInitializedError, ResponseTypeNotSupported


@dataclass(frozen=True)
class CachedResponse:
    data: str | bytes | list | dict
    is_fastapi_response_subclass: bool
    fastapi_response_class: str | None


ResponseType = TypeVar(
    "ResponseType",
)


def get_injected(sig: Signature):
    print(list(sig.parameters.values()))


def encode(data) -> str:
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
    return data_dict["data"]


def cache(ttl: int = 60):
    def wrapper(func: Callable[..., Awaitable[ResponseType]]):
        @wraps(func)
        async def inner(*args, **kwargs) -> ResponseType:
            registry = CacheRegistry.get_instance()
            if not registry:
                raise CacheNotInitializedError(
                    "cache is not initialized and backend is not provided"
                )

            sig = signature(func)
            get_injected(sig)
            cleaner = FunctionCleaner(sig, kwargs)
            kwargs_without_deps = cleaner.get_kwargs_without_injected_deps()
            kwargs_with_deps = cleaner.get_kwargs_with_injected_deps()
            key = convert_func_name_and_args_to_str(
                "app_cache", func, **kwargs_without_deps
            )
            cached = await registry.get_cached(key)
            if not cached:
                cached = await func(*args, **kwargs_with_deps)
                cached = encode(cached)
                await registry.set_key(key, cached, ttl)
            return decode(cached)  # type: ignore

        return inner

    return wrapper
