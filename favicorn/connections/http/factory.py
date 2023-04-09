import asyncio
from typing import Callable

from asgiref.typing import ASGI3Application

from favicorn.iconnection import IConnection
from favicorn.iconnection_factory import IConnectionFactory

from .connection import HTTPConnection
from .parser import HTTPParser
from .serializer import HTTPSerializer


class HTTPConnectionFactory(IConnectionFactory):
    def __init__(
        self,
        app: ASGI3Application,
        parser_factory: Callable[[], HTTPParser],
        serializer_factory: Callable[[], HTTPSerializer],
    ) -> None:
        self.app = app
        self.parser_factory = parser_factory
        self.serializer_factory = serializer_factory

    def build(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> IConnection:
        return HTTPConnection(
            self.app,
            self.parser_factory,
            self.serializer_factory,
            reader,
            writer,
        )
