from abc import ABC, abstractmethod
from typing import AsyncGenerator

from .controller_events import HTTPControllerEvent


class IHTTPController(ABC):
    @abstractmethod
    async def start(
        self,
        initial_data: bytes | None,
    ) -> AsyncGenerator[HTTPControllerEvent, None]:
        raise NotImplementedError

    @abstractmethod
    def receive_data(self, data: bytes | None) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_keepalive(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError


class IHTTPControllerFactory(ABC):
    @abstractmethod
    def build(self, client: tuple[str, int] | None) -> IHTTPController:
        raise NotImplementedError
