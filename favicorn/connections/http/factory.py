import asyncio

from favicorn.iconnection import IConnection
from favicorn.iconnection_factory import IConnectionFactory

from .connection import HTTPConnection
from .icontroller import IHTTPControllerFactory


class HTTPConnectionFactory(IConnectionFactory):
    def __init__(
        self,
        controller_factory: IHTTPControllerFactory,
    ) -> None:
        self.controller_factory = controller_factory

    def build(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> IConnection:
        return HTTPConnection(
            self.controller_factory,
            reader,
            writer,
        )
