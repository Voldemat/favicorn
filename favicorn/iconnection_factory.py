import asyncio
from abc import ABC, abstractmethod

from .iconnection import IConnection


class IConnectionFactory(ABC):
    @abstractmethod
    def build(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> IConnection:
        raise NotImplementedError
