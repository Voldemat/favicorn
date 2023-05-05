from favicorn.controllers.http.asgi import HTTPASGIControllerFactory
from favicorn.controllers.http.iparser import IHTTPParserFactory
from favicorn.controllers.http.iserializer import IHTTPSerializerFactory
from favicorn.controllers.http.response_metadata import ResponseMetadata
from favicorn.i.event_bus import (
    ControllerReceiveEvent,
    ControllerSendEvent,
    IEventBusFactory,
)

import pytest

from __tests__.conftest import event_bus_factories

from ..conftest import (
    parser_factories,
    serializer_factories,
)


@pytest.mark.parametrize("event_bus_factory", event_bus_factories)
@pytest.mark.parametrize("http_parser_factory", parser_factories)
@pytest.mark.parametrize("http_serializer_factory", serializer_factories)
async def test_controller_returns_200(
    event_bus_factory: IEventBusFactory,
    http_parser_factory: IHTTPParserFactory,
    http_serializer_factory: IHTTPSerializerFactory,
) -> None:
    request_bytes = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"

    async def app(scope, receive, send) -> None:  # type: ignore
        assert scope["type"] == "http"
        assert scope["scheme"] == "http"
        assert scope["path"] == "/"
        assert scope["method"] == "GET"
        assert scope["http_version"] == "1.1"
        assert scope["headers"][0] == (b"host", b"localhost")
        assert await receive() == {
            "type": "http.request",
            "body": b"",
            "more_body": False,
        }
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"Content-Length", b"0")],
            }
        )
        await send(
            {"type": "http.response.body", "body": b"", "more_body": False}
        )

    factory = HTTPASGIControllerFactory(
        app,
        http_parser_factory=http_parser_factory,
        serializer_factory=http_serializer_factory,
        event_bus_factory=event_bus_factory,
    )
    serializer = http_serializer_factory.build()
    controller = factory.build()
    event_bus = controller.get_event_bus()
    await controller.start(client=None)
    assert (
        ControllerReceiveEvent(count=None, timeout=None)
        == await event_bus.__anext__()
    )
    event_bus.provide_for_receive(request_bytes)
    expected_res_metadata = ResponseMetadata(
        status=200, headers=((b"Content-Length", b"0"),)
    )
    assert (
        ControllerSendEvent(
            data=serializer.serialize_metadata(expected_res_metadata)
        )
        == await event_bus.__anext__()
    )
    await controller.stop()
    assert controller.is_keepalive()
    assert ControllerSendEvent(data=b"") == await event_bus.__anext__()
    with pytest.raises(StopAsyncIteration):
        await event_bus.__anext__()


@pytest.mark.parametrize("event_bus_factory", event_bus_factories)
@pytest.mark.parametrize("http_parser_factory", parser_factories)
@pytest.mark.parametrize("http_serializer_factory", serializer_factories)
async def test_controller_returns_500_on_exception_in_asgi_callable(
    event_bus_factory: IEventBusFactory,
    http_parser_factory: IHTTPParserFactory,
    http_serializer_factory: IHTTPSerializerFactory,
) -> None:
    async def app(scope, receive, send) -> None:  # type: ignore
        raise Exception()

    factory = HTTPASGIControllerFactory(
        app,
        http_parser_factory=http_parser_factory,
        serializer_factory=http_serializer_factory,
        event_bus_factory=event_bus_factory,
    )
    serializer = http_serializer_factory.build()
    controller = factory.build()
    event_bus = controller.get_event_bus()
    await controller.start(client=None)
    assert (
        ControllerReceiveEvent(count=None, timeout=None)
        == await event_bus.__anext__()
    )
    event_bus.provide_for_receive(b"GET / HTTP/1.0\r\n\r\n")
    expected_res_body = b"Internal Server Error"
    assert (
        ControllerSendEvent(
            data=serializer.serialize_metadata(
                ResponseMetadata(
                    status=500,
                    headers=(
                        (b"Content-Type", b"text/plain; charset=utf-8"),
                        (
                            b"Content-Length",
                            str(len(expected_res_body)).encode(),
                        ),
                    ),
                )
            )
            + serializer.serialize_body(expected_res_body)
        )
        == await event_bus.__anext__()
    )
    await controller.stop()
    assert not controller.is_keepalive()
    with pytest.raises(StopAsyncIteration):
        await event_bus.__anext__()


@pytest.mark.parametrize("event_bus_factory", event_bus_factories)
@pytest.mark.parametrize("http_parser_factory", parser_factories)
@pytest.mark.parametrize("http_serializer_factory", serializer_factories)
async def test_controller_returns_400_on_invalid_http_request(
    event_bus_factory: IEventBusFactory,
    http_parser_factory: IHTTPParserFactory,
    http_serializer_factory: IHTTPSerializerFactory,
) -> None:
    factory = HTTPASGIControllerFactory(
        lambda: None,  # type: ignore[misc,arg-type]
        http_parser_factory=http_parser_factory,
        serializer_factory=http_serializer_factory,
        event_bus_factory=event_bus_factory,
    )
    serializer = http_serializer_factory.build()
    controller = factory.build()
    event_bus = controller.get_event_bus()
    await controller.start(client=None)
    assert (
        ControllerReceiveEvent(count=None, timeout=None)
        == await event_bus.__anext__()
    )
    event_bus.provide_for_receive(b"asdasds/ HTTP/1.0\r\n\r\n")
    expected_res_body = b"Invalid http request"
    assert (
        ControllerSendEvent(
            data=serializer.serialize_metadata(
                ResponseMetadata(
                    status=400,
                    headers=(
                        (b"Content-Type", b"text/plain; charset=utf-8"),
                        (
                            b"Content-Length",
                            str(len(expected_res_body)).encode(),
                        ),
                    ),
                )
            )
            + serializer.serialize_body(expected_res_body)
        )
        == await event_bus.__anext__()
    )
    await controller.stop()
    assert not controller.is_keepalive()
    with pytest.raises(StopAsyncIteration):
        await event_bus.__anext__()
