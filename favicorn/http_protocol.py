import asyncio

from asgiref.typing import ASGI3Application

from .asgi_controller import ASGIController
from .iprotocol import IProtocol
from .request_parser import HTTPRequestParser
from .response_serializer import HTTPResponseSerializer


class HTTPProtocol(IProtocol):
    def __init__(self, app: ASGI3Application) -> None:
        self.app = app

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        if not isinstance(transport, asyncio.Transport):
            raise ValueError("transport must be instance of asyncio.Transport")
        self.request_parser = HTTPRequestParser(transport)
        self.asgi_controller = ASGIController(
            app=self.app,
            request_parser=self.request_parser,
            response_serializer=HTTPResponseSerializer(transport),
        )
        asyncio.create_task(self.asgi_controller.start())

    def connection_lost(self, exc: Exception | None) -> None:
        self.request_parser.disconnect()
        if exc is not None:
            print(exc)

    def data_received(self, data: bytes) -> None:
        self.request_parser.feed_data(data)

    def eof_received(self) -> bool:
        return False
