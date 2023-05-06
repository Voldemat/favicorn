import asyncio
from collections import deque
from typing import Any, AsyncGenerator

from favicorn.i.event_bus import (
    ControllerEvent,
    ControllerReceiveEvent,
    ControllerSendEvent,
    IEventBus,
    IEventBusFactory,
)


class DequeEventBus(IEventBus):
    provider_event: asyncio.Event
    controller_event: asyncio.Event
    provider_queue: deque[bytes | None]
    controller_queue: deque[ControllerEvent | None]

    def __init__(self) -> None:
        self.provider_queue = deque()
        self.controller_queue = deque()
        self.provider_event = asyncio.Event()
        self.controller_event = asyncio.Event()

    def push_to_controller_queue(self, event: ControllerEvent | None) -> None:
        self.controller_queue.append(event)
        self.controller_event.set()

    def push_to_provider_queue(self, data: bytes | None) -> None:
        self.provider_queue.append(data)
        self.provider_event.set()

    def send(self, data: bytes) -> None:
        self.push_to_controller_queue(ControllerSendEvent(data=data))

    async def receive(
        self, count: int | None = None, timeout: float | None = None
    ) -> bytes | None:
        event = ControllerReceiveEvent(count=count, timeout=timeout)
        if event not in self.controller_queue:
            self.push_to_controller_queue(event)
        await self.provider_event.wait()
        if len(self.provider_queue) != 0:
            return self.provider_queue.popleft()
        self.provider_event.clear()
        return await self.receive(count=count, timeout=timeout)

    def __aiter__(self) -> AsyncGenerator[ControllerEvent, None]:
        return self

    async def asend(self, _: None) -> ControllerEvent:
        event = await self.get_event()
        if event is None:
            raise StopAsyncIteration()
        return event

    async def get_event(self) -> ControllerEvent | None:
        await self.controller_event.wait()
        if len(self.controller_queue) != 0:
            return self.controller_queue.popleft()
        self.controller_event.clear()
        return await self.get_event()

    def provide_for_receive(self, data: bytes | None) -> None:
        self.push_to_provider_queue(data)

    def close(self) -> None:
        self.push_to_controller_queue(None)

    async def athrow(self, *args: Any, **kwargs: Any) -> ControllerEvent:
        return await super().athrow(*args, **kwargs)


class DequeEventBusFactory(IEventBusFactory):
    def build(self) -> IEventBus:
        return DequeEventBus()
