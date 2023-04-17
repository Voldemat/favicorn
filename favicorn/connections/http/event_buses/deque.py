import asyncio
from collections import deque
from typing import Any, AsyncGenerator

from ..controller_events import HTTPControllerEvent
from ..ievent_bus import IEventBus, IEventBusFactory


class DequeEventBus(IEventBus):
    provider_event: asyncio.Event
    controller_event: asyncio.Event
    provider_queue: deque[bytes | None]
    controller_queue: deque[HTTPControllerEvent | None]

    def __init__(self) -> None:
        self.provider_queue = deque()
        self.controller_queue = deque()
        self.provider_event = asyncio.Event()
        self.controller_event = asyncio.Event()

    def send(self, data: bytes | None) -> None:
        self.provider_queue.append(data)
        self.provider_event.set()

    async def receive(self) -> bytes | None:
        await self.provider_event.wait()
        if len(self.provider_queue) != 0:
            return self.provider_queue.popleft()
        self.provider_event.clear()
        return await self.receive()

    def dispatch_event(self, event: HTTPControllerEvent) -> None:
        self._dispatch_event(event)

    def _dispatch_event(self, event: HTTPControllerEvent | None) -> None:
        self.controller_queue.append(event)
        self.controller_event.set()

    def __aiter__(self) -> AsyncGenerator[HTTPControllerEvent, None]:
        return self

    async def asend(self, _: None) -> HTTPControllerEvent:
        event = await self.get_event()
        if event is None:
            raise StopAsyncIteration()
        return event

    async def athrow(self, *args: Any, **kwargs: Any) -> HTTPControllerEvent:
        return await super().athrow(*args, **kwargs)

    async def get_event(self) -> HTTPControllerEvent | None:
        await self.controller_event.wait()
        if len(self.controller_queue) != 0:
            return self.controller_queue.popleft()
        self.controller_event.clear()
        return await self.get_event()

    def close(self) -> None:
        self._dispatch_event(None)


class DequeEventBusFactory(IEventBusFactory):
    def build(self) -> IEventBus:
        return DequeEventBus()
