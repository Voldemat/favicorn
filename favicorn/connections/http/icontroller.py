from abc import ABC, abstractmethod

from .ievent_bus import IEventBus


class IHTTPController(ABC):
    @abstractmethod
    async def start(
        self,
        initial_data: bytes | None,
    ) -> IEventBus:
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
