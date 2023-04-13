from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator


@dataclass
class HTTPControllerReceiveEvent:
    pass


@dataclass
class HTTPControllerSendEvent:
    data: bytes


HTTPControllerEvent = HTTPControllerReceiveEvent | HTTPControllerSendEvent


class IHTTPController(ABC):
    @abstractmethod
    async def start(
        self,
        initial_data: bytes | None,
    ) -> AsyncGenerator[HTTPControllerEvent, None]:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def receive_data(self, data: bytes | None) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_keepalive(self) -> bool:
        raise NotImplementedError
