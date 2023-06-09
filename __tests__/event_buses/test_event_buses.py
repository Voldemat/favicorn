import asyncio

from favicorn.i.event_bus import (
    ControllerReceiveEvent,
    ControllerSendEvent,
    IEventBusFactory,
)

import pytest

from ..factories import event_bus_factories


@pytest.mark.parametrize("event_bus_factory", event_bus_factories)
async def test_event_bus(
    event_bus_factory: IEventBusFactory,
) -> None:
    event_bus = event_bus_factory.build()
    receive_task = asyncio.create_task(event_bus.receive())
    empty_receive_event = ControllerReceiveEvent(count=None, timeout=None)
    assert empty_receive_event == await event_bus.__anext__()
    data = b"something"
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(event_bus.receive(), timeout=0.1)
    assert empty_receive_event == await event_bus.__anext__()
    event_bus.provide_for_receive(data)
    assert data == await receive_task
    send_data = b"asdkmlkasd"
    event_bus.send(data=send_data)
    assert ControllerSendEvent(data=send_data) == await event_bus.__anext__()
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(event_bus.__anext__(), timeout=0.1)

    event_bus.close()
    with pytest.raises(StopAsyncIteration):
        await event_bus.__anext__()


@pytest.mark.parametrize("event_bus_factory", event_bus_factories)
async def test_event_bus_dont_closes_when_have_pending_events(
    event_bus_factory: IEventBusFactory,
) -> None:
    event_bus = event_bus_factory.build()
    data = b"somefin"
    event_bus.send(b"somefin")
    event_bus.close()
    assert ControllerSendEvent(data) == await event_bus.__anext__()
    with pytest.raises(StopAsyncIteration):
        await event_bus.__anext__()
