import asyncio
from typing import Callable

from favicorn.iconnection import IConnection
from favicorn.iconnection_factory import IConnectionFactory

from .connection import HTTPConnection
from .icontroller import IHTTPController
from .parser import HTTPParser
from .serializer import HTTPSerializer


class HTTPConnectionFactory(IConnectionFactory):
    def __init__(
        self,
        controller: IHTTPController,
        parser_factory: Callable[[], HTTPParser],
        serializer_factory: Callable[[], HTTPSerializer],
    ) -> None:
        self.controller = controller
        self.parser_factory = parser_factory
        self.serializer_factory = serializer_factory

    def build(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> IConnection:
        return HTTPConnection(
            self.controller,
            self.parser_factory,
            self.serializer_factory,
            reader,
            writer,
        )
