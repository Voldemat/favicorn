import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Literal

import httptools

from .utils import get_remote_addr, is_ssl


@dataclass
class HTTPRequest:
    path: str
    method: str
    root_path: str
    raw_path: bytes
    http_version: str
    query_string: bytes
    client: tuple[str, int] | None
    server: tuple[str, int] | None
    headers: Iterable[tuple[bytes, bytes]]
    scheme: Literal["https"] | Literal["http"]


class HTTPRequestParser:
    request: HTTPRequest | None
    url: bytes | None
    body: bytes | None
    body_event: asyncio.Event
    request_event: asyncio.Event
    headers: list[tuple[bytes, bytes]]
    transport: asyncio.Transport
    latest_received_data_timestamp: datetime | None

    def __init__(
        self,
        transport: asyncio.Transport,
    ) -> None:
        self.parser = httptools.HttpRequestParser(self)
        self.transport = transport
        self.request = None
        self.url = None
        self.body = None
        self.headers = []
        self.body_event = asyncio.Event()
        self.request_event = asyncio.Event()
        self.more_body = True
        self.disconnected = False
        self.latest_received_data_timestamp = None

    def disconnect(self) -> None:
        self.disconnected = True
        self.body_event.set()

    def on_url(self, url: bytes) -> None:
        self.url = url

    def on_header(self, name: bytes, value: bytes) -> None:
        self.headers.append((name.decode().lower().encode(), value))

    def on_headers_complete(self) -> None:
        http_version = self.parser.get_http_version().upper()
        if self.parser.should_upgrade() and http_version == "1.1":
            self.transport.pause_reading()
            self.transport.write(
                b"HTTP/1.1 501\n\n<h1>Server does"
                b" not support websockets connections</h1>"
            )
            self.transport.write_eof()
            return
        assert self.url is not None
        url_object = httptools.parse_url(self.url)
        self.request = HTTPRequest(
            http_version=http_version,
            scheme="http" if not is_ssl(self.transport) else "https",
            path=url_object.path.decode(),
            raw_path=self.url,
            query_string=url_object.query,
            root_path="",
            headers=self.headers,
            server=("localhost", 8000),
            client=get_remote_addr(self.transport),
            method=self.parser.get_method().decode(),
        )
        self.request_event.set()
        self.transport.pause_reading()

    async def get_request(self) -> HTTPRequest:
        if self.request is None:
            await self.request_event.wait()
            self.request_event.clear()
            assert self.request is not None
        return self.request

    def on_body(self, body: bytes) -> None:
        self.body = body
        self.body_event.set()

    async def receive_body(self) -> tuple[bytes | None, bool]:
        if self.disconnected is True:
            return (None, False)
        if self.body is None:
            self.transport.resume_reading()
            await self.body_event.wait()
            self.body_event.clear()
        body = self.body
        self.body = None
        return (body, self.more_body)

    def feed_data(self, data: bytes) -> None:
        self.latest_received_data_timestamp = datetime.now()
        self.parser.feed_data(data)

    def on_message_complete(self) -> None:
        self.more_body = False
        if self.body is None:
            self.body = b""
        self.body_event.set()
