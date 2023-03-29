import asyncio
from abc import abstractmethod
from datetime import datetime
from typing import Any

from asgiref.typing import ASGI3Application


class IProtocol(asyncio.Protocol):
    @abstractmethod
    def __init__(self, app: ASGI3Application) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_app_task(self) -> asyncio.Task[Any]:
        raise NotImplementedError

    @abstractmethod
    def is_keepalive(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_latest_received_data_timestamp(self) -> datetime | None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
