from favicorn.controllers.asgi import ASGIControllerFactory
from favicorn.i.event_bus import (
    ControllerReceiveEvent,
    ControllerSendEvent,
    IEventBusFactory,
)
from favicorn.i.protocols.http.parser import IHTTPParserFactory
from favicorn.i.protocols.http.response_metadata import ResponseMetadata
from favicorn.i.protocols.http.serializer import IHTTPSerializerFactory
from favicorn.i.protocols.websocket.parser import IWebsocketParserFactory
from favicorn.i.protocols.websocket.serializer import (
    IWebsocketSerializerFactory,
)

import pytest

from __tests__.conftest import create_websocket_client_key, safe_async
from __tests__.factories import (
    event_bus_factories,
    http_parser_factories,
    http_serializer_factories,
    websocket_parser_factories,
    websocket_serializer_factories,
)


CONTROLLER_RECEIVE_EVENT = ControllerReceiveEvent(count=None, timeout=None)


@pytest.mark.parametrize("event_bus_factory", event_bus_factories)
@pytest.mark.parametrize("http_parser_factory", http_parser_factories)
@pytest.mark.parametrize("http_serializer_factory", http_serializer_factories)
async def test_controller_not_supporting_websockets(
    event_bus_factory: IEventBusFactory,
    http_parser_factory: IHTTPParserFactory,
    http_serializer_factory: IHTTPSerializerFactory,
) -> None:
    controller = ASGIControllerFactory(
        app=None,  # type: ignore [arg-type]
        event_bus_factory=event_bus_factory,
        http_protocol=(http_parser_factory, http_serializer_factory),
    ).build()
    event_bus = controller.get_event_bus()
    http_serializer = http_serializer_factory.build()
    await safe_async(controller.start(client=None))
    assert CONTROLLER_RECEIVE_EVENT == await safe_async(event_bus.__anext__())
    event_bus.provide_for_receive(
        b"GET / HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Upgrade: websocket\r\n"
        b"Connection: Upgrade\r\n"
        b"Sec-WebSocket-Key: " + create_websocket_client_key() + b"\r\n\r\n"
    )
    expected_res_body = b"Websockets protocol is unavailable"
    assert ControllerSendEvent(
        data=http_serializer.serialize_metadata(
            ResponseMetadata(
                status=400,
                headers=(
                    (b"Content-Type", b"text/plain; charset=utf-8"),
                    (b"Content-Length", str(len(expected_res_body)).encode()),
                ),
            )
        )
        + http_serializer.serialize_body(expected_res_body)
    ) == await safe_async(event_bus.__anext__())


@pytest.mark.parametrize("event_bus_factory", event_bus_factories)
@pytest.mark.parametrize("http_parser_factory", http_parser_factories)
@pytest.mark.parametrize("http_serializer_factory", http_serializer_factories)
@pytest.mark.parametrize(
    "websocket_parser_factory", websocket_parser_factories
)
@pytest.mark.parametrize(
    "websocket_serializer_factory", websocket_serializer_factories
)
async def test_controller_supporting_websockets(
    event_bus_factory: IEventBusFactory,
    http_parser_factory: IHTTPParserFactory,
    http_serializer_factory: IHTTPSerializerFactory,
    websocket_parser_factory: IWebsocketParserFactory,
    websocket_serializer_factory: IWebsocketSerializerFactory,
) -> None:
    async def app(  # type: ignore[no-untyped-def]
        scope, receive, send
    ) -> None:
        assert scope["type"] == "websocket"
        event = await receive()
        assert event["type"] == "websocket.connect"
        await send(
            {"type": "websocket.accept", "subprotocol": None, "headers": []}
        )
        event = await receive()
        assert event["type"] == "websocket.receive"
        assert event["bytes"] == b"Hello websocket"
        assert event["text"] is None
        await send({"type": "websocket.close", "code": 1000})

    controller = ASGIControllerFactory(
        app=app,
        event_bus_factory=event_bus_factory,
        http_protocol=(http_parser_factory, http_serializer_factory),
        websocket_protocol=(
            websocket_parser_factory,
            websocket_serializer_factory,
        ),
    ).build()
    event_bus = controller.get_event_bus()
    http_serializer = http_serializer_factory.build()
    websocket_serializer = websocket_serializer_factory.build()
    client_websocket_serializer = websocket_serializer_factory.build(
        is_client=True
    )
    await safe_async(controller.start(client=None))

    assert CONTROLLER_RECEIVE_EVENT == await safe_async(event_bus.__anext__())
    sec_websocket_key = create_websocket_client_key()
    sec_websocket_accept = websocket_serializer.create_accept_token(
        sec_websocket_key
    )
    event_bus.provide_for_receive(
        b"GET / HTTP/1.1\r\n"
        b"Host: localhost\r\n"
        b"Upgrade: websocket\r\n"
        b"Connection: Upgrade\r\n"
        b"Sec-WebSocket-Key: " + sec_websocket_key + b"\r\n\r\n"
    )
    assert ControllerSendEvent(
        data=http_serializer.serialize_metadata(
            ResponseMetadata(
                status=101,
                headers=(
                    (b"Connection", b"Upgrade"),
                    (b"Upgrade", b"websocket"),
                    (b"Sec-WebSocket-Accept", sec_websocket_accept),
                ),
            )
        )
    ) == await safe_async(event_bus.__anext__())
    assert CONTROLLER_RECEIVE_EVENT == await safe_async(event_bus.__anext__())
    event_bus.provide_for_receive(
        client_websocket_serializer.serialize_data(b"Hello websocket")
    )
    assert ControllerSendEvent(
        data=websocket_serializer.build_close_frame()
    ) == await safe_async(event_bus.__anext__())
    await safe_async(controller.stop())
    with pytest.raises(StopAsyncIteration):
        await safe_async(event_bus.__anext__())
