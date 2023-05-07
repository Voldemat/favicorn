import asyncio
from typing import Awaitable, TypeVar


T = TypeVar("T")


def safe_async(aw: Awaitable[T], timeout: float = 1) -> Awaitable[T]:
    return asyncio.wait_for(aw, timeout=timeout)
