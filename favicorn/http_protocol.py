import asyncio
from datetime import datetime
from typing import Any

from asgiref.typing import ASGI3Application

from .asgi_controller import ASGIController
from .iprotocol import IProtocol
from .request_parser import HTTPRequestParser
from .response_serializer import HTTPResponseSerializer


class HTTPProtocol(IProtocol):
    latest_received_data_timestamp: datetime | None

    def __init__(self, app: ASGI3Application) -> None:
        self.app = app
        self.latest_received_data_timestamp = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        if not isinstance(transport, asyncio.Transport):
            raise ValueError("transport must be instance of asyncio.Transport")
        self.request_parser = HTTPRequestParser(transport)
        self.response_serializer = HTTPResponseSerializer(transport)
        self.asgi_controller = ASGIController(
            app=self.app,
            request_parser=self.request_parser,
            response_serializer=self.response_serializer,
        )
        self.task = asyncio.create_task(self.asgi_controller.start())
        self.transport = transport

    def connection_lost(self, exc: Exception | None) -> None:
        self.request_parser.disconnect()
        if exc is not None:
            print(exc)
        self.transport.close()

    def data_received(self, data: bytes) -> None:
        self.latest_received_data_timestamp = datetime.now()
        self.request_parser.feed_data(data)

    def eof_received(self) -> bool:
        return False

    def get_app_task(self) -> asyncio.Task[Any]:
        return self.task

    def is_keepalive(self) -> bool:
        return self.response_serializer.keepalive

    def get_latest_received_data_timestamp(self) -> datetime | None:
        return self.latest_received_data_timestamp

    def close(self) -> None:
        self.transport.write_eof()
