import asyncio
from abc import ABC, abstractmethod


class IConnectionManager(ABC):
    @abstractmethod
    async def handler(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        raise NotImplementedError
