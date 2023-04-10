import asyncio
from typing import Callable

from favicorn.iconnection import IConnection
from favicorn.iconnection_factory import IConnectionFactory

from .connection import HTTPConnection
from .icontroller_factory import IHTTPControllerFactory
from .parser import HTTPParser
from .serializer import HTTPSerializer


class HTTPConnectionFactory(IConnectionFactory):
    def __init__(
        self,
        controller_factory: IHTTPControllerFactory,
        parser_factory: Callable[[], HTTPParser],
        serializer_factory: Callable[[], HTTPSerializer],
    ) -> None:
        self.parser_factory = parser_factory
        self.controller_factory = controller_factory
        self.serializer_factory = serializer_factory

    def build(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> IConnection:
        return HTTPConnection(
            self.controller_factory,
            self.parser_factory,
            self.serializer_factory,
            reader,
            writer,
        )
