from favicorn.iconnection import IConnection
from favicorn.reader import SocketReader
from favicorn.writer import SocketWriter

from .controller_events import (
    HTTPControllerReceiveEvent,
    HTTPControllerSendEvent,
)
from .icontroller import IHTTPControllerFactory


class HTTPConnection(IConnection):
    def __init__(
        self,
        controller_factory: IHTTPControllerFactory,
        reader: SocketReader,
        writer: SocketWriter,
        keepalive_timeout_s: int = 5,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.keepalive = True
        self.client = writer.get_address()
        self.controller_factory = controller_factory
        self.keepalive_timeout_s = keepalive_timeout_s

    async def init(self) -> None:
        pass

    async def main(self) -> None:
        await self.process_request()
        while self.keepalive:
            if await self.reader.wait(timeout=self.keepalive_timeout_s):
                await self.process_request()
            else:
                self.keepalive = False

    async def process_request(self) -> None:
        controller = self.controller_factory.build()
        event_bus = await controller.start(client=self.client)
        print(event_bus)
        async for event in event_bus:
            if isinstance(event, HTTPControllerReceiveEvent):
                event_bus.send(await self.reader.read(count=event.count))
            elif isinstance(event, HTTPControllerSendEvent):
                self.writer.write(event.data)
            else:
                raise ValueError(f"Unhandled event type {type(event)}")
        self.keepalive = (
            not self.writer.is_closing() and controller.is_keepalive()
        )
        await self.writer.flush()

    async def close(self) -> None:
        await self.writer.close()
