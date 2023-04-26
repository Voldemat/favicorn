from favicorn.iconnection import IConnection, IConnectionFactory
from favicorn.reader import SocketReader
from favicorn.writer import SocketWriter

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
        reader: SocketReader,
        writer: SocketWriter,
    ) -> IConnection:
        return HTTPConnection(
            self.controller_factory,
            reader,
            writer,
        )
