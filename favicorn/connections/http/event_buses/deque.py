import asyncio
from collections import deque
from typing import Any, AsyncGenerator

from ..controller_events import (
    HTTPControllerEvent,
    HTTPControllerReceiveEvent,
    HTTPControllerSendEvent,
)
from ..ievent_bus import IHTTPEventBus, IHTTPEventBusFactory


class HTTPDequeEventBus(IHTTPEventBus):
    provider_event: asyncio.Event
    controller_event: asyncio.Event
    provider_queue: deque[bytes | None]
    controller_queue: deque[HTTPControllerEvent | None]

    def __init__(self) -> None:
        self.provider_queue = deque()
        self.controller_queue = deque()
        self.provider_event = asyncio.Event()
        self.controller_event = asyncio.Event()

    def send(self, data: bytes) -> None:
        self.push_to_controller_queue(HTTPControllerSendEvent(data=data))

    async def receive(
        self, count: int | None = None, timeout: float | None = None
    ) -> bytes | None:
        self.push_to_controller_queue(
            HTTPControllerReceiveEvent(count=count, timeout=timeout)
        )
        await self.provider_event.wait()
        if len(self.provider_queue) != 0:
            return self.provider_queue.popleft()
        self.provider_event.clear()
        return await self.receive(count=count, timeout=timeout)

    def __aiter__(self) -> AsyncGenerator[HTTPControllerEvent, None]:
        return self

    async def asend(self, _: None) -> HTTPControllerEvent:
        event = await self.get_event()
        if event is None:
            raise StopAsyncIteration()
        return event

    async def athrow(self, *args: Any, **kwargs: Any) -> HTTPControllerEvent:
        return await super().athrow(*args, **kwargs)

    def provide_for_receive(self, data: bytes | None) -> None:
        self.push_to_provider_queue(data)

    def push_to_provider_queue(self, data: bytes | None) -> None:
        self.provider_queue.append(data)
        self.provider_event.set()

    def push_to_controller_queue(
        self, event: HTTPControllerEvent | None
    ) -> None:
        self.controller_queue.append(event)
        self.controller_event.set()

    async def get_event(self) -> HTTPControllerEvent | None:
        await self.controller_event.wait()
        if len(self.controller_queue) != 0:
            return self.controller_queue.popleft()
        self.controller_event.clear()
        return await self.get_event()

    def close(self) -> None:
        self.push_to_controller_queue(None)


class HTTPDequeEventBusFactory(IHTTPEventBusFactory):
    def build(self) -> IHTTPEventBus:
        return HTTPDequeEventBus()
