import asyncio

from .request_parser import HTTPRequestParser


class HTTPProtocol(asyncio.Protocol):
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        if not isinstance(transport, asyncio.Transport):
            raise ValueError("transport must be instance of asyncio.Transport")
        self.parser = HTTPRequestParser(transport)

    def connection_lost(self, exc: Exception | None) -> None:
        print(exc)

    def data_received(self, data: bytes) -> None:
        self.parser.feed_data(data)

    def eof_received(self) -> bool:
        return False
