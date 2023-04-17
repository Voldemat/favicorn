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
        default_read_batch: int = 4028,
        keepalive_timeout_s: int = 5,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.keepalive = True
        self.client = get_remote_addr(writer)
        self.controller_factory = controller_factory
        self.default_read_batch = default_read_batch
        self.keepalive_timeout_s = keepalive_timeout_s

    async def init(self) -> None:
        pass

    async def main(self) -> None:
        while self.keepalive:
            data = await self.read(timeout=self.keepalive_timeout_s)
            if data is None:
                self.keepalive = False
                continue
            await self.handle_request(data)

    async def handle_request(self, data: bytes) -> None:
        controller = self.controller_factory.build(client=self.client)
        event_bus = await controller.start(initial_data=data)
        async for event in event_bus:
            if isinstance(event, HTTPControllerReceiveEvent):
                event_bus.send(await self.read(count=event.count))
            elif isinstance(event, HTTPControllerSendEvent):
                self.writer.write(event.data)
            else:
                raise ValueError(f"Unhandled event type {type(event)}")
        if self.writer.is_closing():
            self.keepalive = False
            return
        self.keepalive = controller.is_keepalive()
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
            count = self.default_read_batch
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
