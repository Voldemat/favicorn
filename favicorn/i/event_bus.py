from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator


@dataclass
class ControllerReceiveEvent:
    count: int | None
    timeout: float | None


@dataclass
class ControllerSendEvent:
    data: bytes


ControllerEvent = ControllerReceiveEvent | ControllerSendEvent


class IEventBus(ABC, AsyncGenerator[ControllerEvent, None]):
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


class IEventBusFactory(ABC):
    @abstractmethod
    def build(self) -> IEventBus:
        raise NotImplementedError
