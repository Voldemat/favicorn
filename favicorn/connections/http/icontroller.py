from abc import ABC, abstractmethod

from .ievent_bus import IHTTPEventBus


class IHTTPController(ABC):
    @abstractmethod
    async def start(
        self,
        client: tuple[str, int] | None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_keepalive(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError


class IHTTPControllerFactory(ABC):
    @abstractmethod
    def build(self) -> tuple[IHTTPController, IHTTPEventBus]:
        raise NotImplementedError
