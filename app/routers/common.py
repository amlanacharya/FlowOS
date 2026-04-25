from collections.abc import Awaitable, Callable
from typing import TypeVar

from fastapi import HTTPException

T = TypeVar("T")


async def bad_request_on_value_error(operation: Callable[[], Awaitable[T]]) -> T:
    try:
        return await operation()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
