import asyncio
from typing import Callable, overload

from asgiref.typing import ASGI3Application

from favicorn.asgi_controller import ASGIController
from favicorn.iconnection import IConnection
from favicorn.utils import get_remote_addr

from .parser import HTTPParser
from .serializer import HTTPSerializer


class HTTPConnection(IConnection):
    def __init__(
        self,
        app: ASGI3Application,
        parser_class: Callable[[], HTTPParser],
        serializer_class: Callable[[], HTTPSerializer],
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.app = app
        self.parser_class = parser_class
        self.serializer_class = serializer_class
        self.client = get_remote_addr(writer)
        self.keepalive = True

    async def init(self) -> None:
        pass

    async def main(self) -> None:
        while self.keepalive:
            data = await self.read(timeout=5)
            if data is None:
                break
            await self.handle_request(data)

    async def handle_request(self, data: bytes) -> None:
        asgi_controller = ASGIController(
            self.app,
            root_path="",
            client=self.client,
            server=("localhost", 8000),
        )
        parser = self.parser_class()
        serializer = self.serializer_class()
        parser.feed_data(data)
        while not parser.state.is_metadata_ready():
            data = await self.read()
            if data is None:
                return
            parser.feed_data(data)

        metadata = parser.state.get_metadata()
        async for event in asgi_controller.start(metadata):
            if event["type"] == "receive":
                if not parser.has_body():
                    data = await self.read()
                    if data is None:
                        asgi_controller.disconnect()
                    else:
                        parser.feed_data(data)
                body = parser.get_body()
                assert body is not None
                asgi_controller.receive_body(body, parser.state.more_body)
            if event["type"] == "send-metadata":
                serializer.receive_metadata(event["metadata"])
                data = serializer.get_data()
                self.write(data)
            if event["type"] == "send-body":
                serializer.feed_body(event["body"], event["more_body"])
                data = serializer.get_data()
                self.write(data)

        await asgi_controller.stop()
        self.keepalive = (
            not self.writer.is_closing() and parser.state.is_keepalive()
        )
        if not self.writer.is_closing():
            await self.writer.drain()
        parser.reset()
        serializer.reset()

    @overload
    async def read(self, timeout: None = None) -> bytes:
        ...

    @overload
    async def read(self, timeout: int) -> bytes | None:
        ...

    async def read(self, timeout: int | None = None) -> bytes | None:
        if timeout is None:
            return await self._read()
        try:
            return await asyncio.wait_for(self._read(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def _read(self) -> bytes | None:
        data = await self.reader.read(4028)
        if self.reader.at_eof():
            return None
        return data

    def write(self, data: bytes) -> None:
        self.writer.write(data)

    async def close(self) -> None:
        if self.writer.is_closing():
            return
        if self.writer.can_write_eof():
            self.writer.write_eof()
        self.writer.close()
        await self.writer.wait_closed()
