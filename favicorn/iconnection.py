import asyncio
from abc import ABC, abstractmethod


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
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> IConnection:
        raise NotImplementedError
