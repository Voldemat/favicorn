from abc import ABC, abstractmethod

from .reader import SocketReader
from .writer import SocketWriter


class IConnection(ABC):
    @abstractmethod
    async def init(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def main(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError


class IConnectionFactory(ABC):
    @abstractmethod
    def build(
        self,
        reader: SocketReader,
        writer: SocketWriter,
    ) -> IConnection:
        raise NotImplementedError
