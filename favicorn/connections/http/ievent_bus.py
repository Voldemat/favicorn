from abc import ABC, abstractmethod
from typing import AsyncGenerator

from .controller_events import HTTPControllerEvent


class IHTTPEventBus(ABC, AsyncGenerator[HTTPControllerEvent, None]):
    @abstractmethod
    def send(self, data: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    async def receive(
        self, count: int | None = None, timeout: float | None = None
    ) -> bytes | None:
        raise NotImplementedError

    @abstractmethod
    def provide_for_receive(self, data: bytes | None) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class IHTTPEventBusFactory(ABC):
    @abstractmethod
    def build(self) -> IHTTPEventBus:
        raise NotImplementedError
