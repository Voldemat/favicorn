import asyncio

from asgiref.typing import ASGIReceiveCallable, ASGISendCallable, HTTPScope

from .conftest import serving_app


async def app(
    scope: HTTPScope, receive: ASGIReceiveCallable, send: ASGISendCallable
) -> None:
    await send(
        {
            "type": "http.response.start",
            "headers": [],
            "trailers": False,
            "status": 200,
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": b"",
            "more_body": False,
        }
    )


class TestProtocol(asyncio.Protocol):
    __test__ = False

    def __init__(self, response_event: asyncio.Event, keepalive: bool) -> None:
        self.response_event = response_event
        self.keepalive = keepalive

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        assert isinstance(transport, asyncio.Transport)
        self.transport = transport
        message = b"GET / HTTP/1.1\r\n"
        if self.keepalive is False:
            message += b"Connection: close\r\n"
        message += b"\r\n"
        self.transport.write(message)

    def connection_lost(self, exc: Exception | None) -> None:
        self.response_event.set()

    def data_received(self, data: bytes) -> None:
        assert b"HTTP/1.1 200 OK" in data
        self.response_event.set()


async def test_keepalive_on() -> None:
    host = "localhost"
    port = 8000
    with serving_app(app, host=host, port=port):
        loop = asyncio.get_running_loop()
        response_event = asyncio.Event()

        transport, protocol = await loop.create_connection(
            lambda: TestProtocol(response_event, keepalive=True),
            host=host,
            port=port,
        )
        await response_event.wait()
        await asyncio.sleep(0)
        assert transport.is_closing() is False
        await asyncio.sleep(5.1)
        assert transport.is_closing() is True


async def test_keepalive_off() -> None:
    host = "localhost"
    port = 8000
    with serving_app(app, host=host, port=port):
        loop = asyncio.get_running_loop()
        response_event = asyncio.Event()

        transport, protocol = await loop.create_connection(
            lambda: TestProtocol(response_event, keepalive=False),
            host=host,
            port=port,
        )
        await response_event.wait()
        await asyncio.sleep(0)
        await asyncio.sleep(1)
        assert transport.is_closing() is True
