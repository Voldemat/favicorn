from abc import ABC, abstractmethod
from typing import AsyncGenerator

from .controller_events import HTTPControllerEvent


class IEventBus(ABC, AsyncGenerator[HTTPControllerEvent, None]):
    @abstractmethod
    def dispatch_event(self, event: HTTPControllerEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    def send(self, data: bytes | None) -> None:
        raise NotImplementedError

    @abstractmethod
    async def receive(self) -> bytes | None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class IEventBusFactory(ABC):
    @abstractmethod
    def build(self) -> IEventBus:
        raise NotImplementedError
