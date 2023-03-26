import asyncio

from asgiref.typing import (
    ASGIVersions,
    HTTPScope,
)

import httptools

from .utils import get_remote_addr, is_ssl


class URL:
    schema: bytes
    host: bytes
    port: int
    path: bytes
    query: bytes
    fragment: bytes
    userinfo: bytes
    raw_url: bytes

    def __init__(self, raw_url: bytes) -> None:
        obj = httptools.parse_url(raw_url)
        self.raw_url = raw_url
        self.schema = obj.schema
        self.host = obj.host
        self.port = obj.port
        self.path = obj.path
        self.query = obj.query
        self.fragment = obj.fragment
        self.userinfo = obj.userinfo


class HTTPRequestParser:
    scope: HTTPScope | None
    url: URL | None
    body: bytes | None
    body_event: asyncio.Event
    scope_event: asyncio.Event
    headers: list[tuple[bytes, bytes]]
    is_completed: bool
    transport: asyncio.Transport

    def __init__(
        self,
        transport: asyncio.Transport,
    ) -> None:
        self.parser = httptools.HttpRequestParser(self)
        self.transport = transport
        self.scope = None
        self.url = None
        self.body = None
        self.headers = []
        self.body_event = asyncio.Event()
        self.scope_event = asyncio.Event()
        self.is_completed = False

    def disconnect(self) -> None:
        self.is_completed = True

    def on_url(self, url: bytes) -> None:
        self.url = URL(url)

    def on_header(self, name: bytes, value: bytes) -> None:
        self.headers.append((name.decode().lower().encode(), value))

    def on_headers_complete(self) -> None:
        if self.parser.should_upgrade():
            self.transport.pause_reading()
            self.transport.write(
                b"HTTP/1.1 501\n\n<h1>Server does"
                b" not support websockets connections</h1>"
            )
            self.transport.write_eof()
        assert self.url is not None
        self.scope = HTTPScope(
            type="http",
            asgi=ASGIVersions(spec_version="3.0", version="3.0"),
            http_version=self.parser.get_http_version().upper(),
            scheme="http" if not is_ssl(self.transport) else "https",
            path=self.url.path.decode(),
            raw_path=self.url.raw_url,
            query_string=self.url.query,
            root_path="",
            headers=self.headers,
            server=("localhost", 8000),
            client=get_remote_addr(self.transport),
            extensions={},
            method=self.parser.get_method().decode(),
        )
        self.scope_event.set()
        self.transport.pause_reading()

    async def get_scope(self) -> HTTPScope:
        if self.scope is None:
            await self.scope_event.wait()
            self.scope_event.clear()
            assert self.scope is not None
        return self.scope

    def on_body(self, body: bytes) -> None:
        if self.body is None:
            self.body = b""
        self.body += body
        self.body_event.set()

    async def receive_body(self) -> tuple[bytes | None, bool]:
        if self.is_completed is True and self.body is None:
            return (self.body, False)
        if self.body is None:
            self.transport.resume_reading()
            await self.body_event.wait()
            self.body_event.clear()
        return (self.body, not self.is_completed)

    def feed_data(self, data: bytes) -> None:
        self.parser.feed_data(data)

    def on_message_complete(self) -> None:
        self.is_completed = True
