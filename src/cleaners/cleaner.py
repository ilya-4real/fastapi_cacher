from dataclasses import dataclass, field
from inspect import Signature
from typing import Any

from fastapi import Request, Response


@dataclass
class FunctionCleaner:
    signature: Signature
    function_kwargs: dict[str, Any]
    kwargs_without_deps: dict[str, Any] = field(init=False)
    request: Request = field(init=False)
    response: Response = field(init=False)

    def get_kwargs_without_injected_deps(self) -> dict[str, Any]:
        function_kwargs_with_deps = self.function_kwargs.copy()
        for name, parameter in self.signature.parameters.items():
            if parameter.annotation is Request:
                self.request = function_kwargs_with_deps.pop(name)
            if parameter.annotation is Response:
                self.response = function_kwargs_with_deps.pop(name)
        self.kwargs_without_deps = function_kwargs_with_deps
        return self.kwargs_without_deps

    def get_kwargs_with_injected_deps(self) -> dict[str, Any]:
        return self.function_kwargs

    def get_response_raw_headers(self) -> list[tuple[bytes, bytes]]:
        return self.response.raw_headers
