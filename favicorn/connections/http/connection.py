import asyncio
from typing import Callable, overload

from favicorn.iconnection import IConnection
from favicorn.utils import get_remote_addr

from .icontroller import (
    HTTPControllerReceiveEvent,
    HTTPControllerSendBodyEvent,
    HTTPControllerSendMetadataEvent,
    IHTTPController,
)
from .parser import HTTPParser
from .serializer import HTTPSerializer


class HTTPConnection(IConnection):
    def __init__(
        self,
        controller: IHTTPController,
        parser_factory: Callable[[], HTTPParser],
        serializer_factory: Callable[[], HTTPSerializer],
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.client = get_remote_addr(writer)
        self.controller = controller
        self.parser_factory = parser_factory
        self.serializer_factory = serializer_factory
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
        parser = self.parser_factory()
        serializer = self.serializer_factory()
        parser.feed_data(data)
        while not parser.is_metadata_ready():
            data = await self.read()
            if data is None:
                return
            parser.feed_data(data)

        metadata = parser.get_metadata()
        async for event in self.controller.start(metadata, self.client):
            if isinstance(event, HTTPControllerReceiveEvent):
                if not parser.has_body():
                    if data := await self.read():
                        parser.feed_data(data)
                    else:
                        self.controller.disconnect()
                        continue
                self.controller.receive_body(
                    parser.get_body(), parser.is_more_body()
                )
            elif isinstance(event, HTTPControllerSendMetadataEvent):
                serializer.receive_metadata(event.metadata)
                self.write(serializer.get_data())
            elif isinstance(event, HTTPControllerSendBodyEvent):
                serializer.feed_body(event.body)
                self.write(serializer.get_data())
            else:
                raise ValueError(f"Unhandled event type {type(event)}")

        await self.controller.stop()
        self.keepalive = not self.writer.is_closing() and parser.is_keepalive()
        if not self.writer.is_closing():
            await self.writer.drain()

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
