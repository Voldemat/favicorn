import asyncio
from typing import overload

from favicorn.iconnection import IConnection
from favicorn.utils import get_remote_addr

from .controller_events import (
    HTTPControllerReceiveEvent,
    HTTPControllerSendEvent,
)
from .icontroller import IHTTPControllerFactory


class HTTPConnection(IConnection):
    def __init__(
        self,
        controller_factory: IHTTPControllerFactory,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.controller_factory = controller_factory
        self.client = get_remote_addr(writer)
        self.keepalive = True

    async def init(self) -> None:
        pass

    async def main(self) -> None:
        while self.keepalive:
            if data := await self.read(timeout=5):
                await self.handle_request(data)
            else:
                self.keepalive = False

    async def handle_request(self, data: bytes) -> None:
        controller = self.controller_factory.build(client=self.client)
        async for event in await controller.start(initial_data=data):
            if isinstance(event, HTTPControllerReceiveEvent):
                data = await self.read(count=event.count)
                controller.receive_data(data)
            elif isinstance(event, HTTPControllerSendEvent):
                self.writer.write(event.data)
            else:
                raise ValueError(f"Unhandled event type {type(event)}")
        self.keepalive = (
            not self.writer.is_closing() and controller.is_keepalive()
        )
        if not self.writer.is_closing():
            await self.writer.drain()

    @overload
    async def read(
        self, timeout: None = None, count: int | None = None
    ) -> bytes:
        ...

    @overload
    async def read(
        self, timeout: int, count: int | None = None
    ) -> bytes | None:
        ...

    async def read(
        self, timeout: int | None = None, count: int | None = None
    ) -> bytes | None:
        if timeout is None:
            return await self._read(count=count)
        try:
            return await asyncio.wait_for(
                self._read(count=count), timeout=timeout
            )
        except asyncio.TimeoutError:
            return None

    async def _read(self, count: int | None = None) -> bytes | None:
        if count is None:
            count = 4028
        data = await self.reader.read(count)
        if self.reader.at_eof():
            return None
        return data

    def write(self, data: bytes) -> None:
        if not self.writer.is_closing():
            self.writer.write(data)

    async def close(self) -> None:
        if self.writer.is_closing():
            return
        if self.writer.can_write_eof():
            self.writer.write_eof()
        self.writer.close()
        await self.writer.wait_closed()
