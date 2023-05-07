import asyncio
import base64
import os
from typing import Awaitable, TypeVar


T = TypeVar("T")


def safe_async(aw: Awaitable[T], timeout: float = 1) -> Awaitable[T]:
    return asyncio.wait_for(aw, timeout=timeout)


def create_websocket_client_key() -> bytes:
    return base64.b64encode(os.urandom(16))
