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
        await self.process_request()

    async def main(self) -> None:
        while self.keepalive:
            if data := await self.reader.read(
                timeout=self.keepalive_timeout_s
            ):
                await self.process_request(data)
            else:
                self.keepalive = False

    async def process_request(self, data: bytes | None = None) -> None:
        controller = self.controller_factory.build(client=self.client)
        event_bus = await controller.start(initial_data=data)
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
