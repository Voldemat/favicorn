from abc import ABC, abstractmethod

from .config import Config
from .iprotocol import IProtocol


class IGlobalState(ABC):
    @abstractmethod
    def get_config(self) -> Config:
        pass

    @abstractmethod
    def add_connection(self, connection: IProtocol) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_connections(self) -> list[IProtocol]:
        raise NotImplementedError

    @abstractmethod
    async def discard_all_connections(self) -> None:
        raise NotImplementedError
