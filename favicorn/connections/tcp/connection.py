from favicorn.i.connection import IConnection, IConnectionFactory
from favicorn.i.controller import IControllerFactory
from favicorn.i.event_bus import (
    ControllerReceiveEvent,
    ControllerSendEvent,
    IEventBus,
)
from favicorn.reader import SocketReader
from favicorn.writer import SocketWriter


class TCPConnection(IConnection):
    def __init__(
        self,
        reader: SocketReader,
        writer: SocketWriter,
        controller_factory: IControllerFactory,
        keepalive_timeout_s: float,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.keepalive = True
        self.client = writer.get_address()
        self.controller_factory = controller_factory
        self.keepalive_timeout_s = keepalive_timeout_s

    async def main(self) -> None:
        while (
            not self.writer.is_closing()
            and self.keepalive
            and await self.reader.wait(timeout=self.keepalive_timeout_s)
        ):
            await self.process_request()

    async def process_request(self) -> None:
        controller = self.controller_factory.build()
        event_bus = controller.get_event_bus()
        await controller.start(client=self.client)
        try:
            await self.process_controller_events(event_bus)
            self.keepalive = controller.is_keepalive()
        finally:
            await controller.stop()
            await self.writer.flush()

    async def process_controller_events(self, event_bus: IEventBus) -> None:
        async for event in event_bus:
            if isinstance(event, ControllerReceiveEvent):
                event_bus.provide_for_receive(
                    await self.reader.read(
                        count=event.count, timeout=event.timeout
                    )
                )
            elif isinstance(event, ControllerSendEvent):
                self.writer.write(event.data)
            else:
                raise ValueError(f"Unhandled event type {type(event)}")

    async def close(self) -> None:
        await self.writer.close()


class TCPConnectionFactory(IConnectionFactory):
    def __init__(
        self,
        controller_factory: IControllerFactory,
        keepalive_timeout_s: float = 5,
    ) -> None:
        self.controller_factory = controller_factory
        self.keepalive_timeout_s = keepalive_timeout_s

    def build(
        self,
        reader: SocketReader,
        writer: SocketWriter,
    ) -> IConnection:
        return TCPConnection(
            reader=reader,
            writer=writer,
            controller_factory=self.controller_factory,
            keepalive_timeout_s=self.keepalive_timeout_s,
        )
