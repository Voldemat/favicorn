from abc import ABC, abstractmethod

from .event_bus import IEventBus


class IController(ABC):
    @abstractmethod
    async def start(
        self,
        client: tuple[str, int] | None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_event_bus(self) -> IEventBus:
        raise NotImplementedError

    @abstractmethod
    def is_keepalive(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError


class IControllerFactory(ABC):
    @abstractmethod
    def build(self) -> IController:
        raise NotImplementedError
