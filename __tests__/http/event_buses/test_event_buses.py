import asyncio

from favicorn.connections.http.controller_events import (
    HTTPControllerReceiveEvent,
    HTTPControllerSendEvent,
)
from favicorn.connections.http.ievent_bus import IHTTPEventBusFactory

import pytest

from ..conftest import event_bus_factories


@pytest.mark.parametrize("event_bus_factory", event_bus_factories)
async def test_event_bus(
    event_bus_factory: IHTTPEventBusFactory,
) -> None:
    event_bus = event_bus_factory.build()
    receive_event = HTTPControllerReceiveEvent(count=None, timeout=None)
    event_bus.dispatch_event(receive_event)
    assert receive_event == await event_bus.__anext__()
    data = b"something"
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(event_bus.receive(), timeout=0.1)
    event_bus.send(data)
    assert data == await event_bus.receive()
    send_event = HTTPControllerSendEvent(data=b"asdkmlkasd")
    event_bus.dispatch_event(send_event)
    assert send_event == await event_bus.__anext__()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(event_bus.__anext__(), timeout=0.1)

    event_bus.close()
    with pytest.raises(StopAsyncIteration):
        await event_bus.__anext__()
