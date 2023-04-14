from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import httptools

from ..iparser import IHTTPParser
from ..request_metadata import RequestMetadata


@dataclass
class HTTPParserState:
    more_body: bool = True
    body: bytes | None = None
    method: str | None = None
    raw_url: bytes | None = None
    http_version: str | None = None
    headers: list[tuple[bytes, bytes]] = field(default_factory=list)
    request_connection_close: bool | None = None

    def is_metadata_ready(self) -> bool:
        return (
            self.raw_url is not None
            and self.method is not None
            and self.http_version is not None
        )

    def get_metadata(self) -> RequestMetadata:
        assert self.raw_url is not None
        assert self.method is not None
        assert self.http_version is not None
        url = httptools.parse_url(self.raw_url)
        return RequestMetadata(
            raw_path=url.path,
            method=self.method,
            headers=self.headers,
            path=url.path.decode(),
            query_string=url.query,
            http_version=self.http_version,
            is_keepalive=self.is_keepalive(),
        )

    def add_header(self, name: bytes, value: bytes) -> None:
        self.headers.append((name, value))
        if name.decode().lower() == "connection":
            self.request_connection_close = value.decode().lower() == "close"

    def is_keepalive(self) -> bool:
        if self.request_connection_close is None:
            return self.http_version != "1.0"
        return self.request_connection_close is False


class HTTPToolsParser(IHTTPParser):
    state: HTTPParserState
    parser: httptools.HttpRequestParser

    def __init__(self) -> None:
        self.parser = httptools.HttpRequestParser(self)
        self.state = HTTPParserState()
        self.body_event = asyncio.Event()
        self.headers_event = asyncio.Event()
        self.message_start_event = asyncio.Event()
        self.disconnected = False

    def on_message_begin(self) -> None:
        self.state = HTTPParserState()
        self.message_start_event.set()

    def on_url(self, url: bytes) -> None:
        self.state.raw_url = url

    def on_header(self, name: bytes, value: bytes) -> None:
        self.state.add_header(name, value)

    def on_headers_complete(self) -> None:
        self.state.http_version = self.parser.get_http_version()
        self.state.method = self.parser.get_method().decode().upper()
        self.headers_event.set()

    def on_body(self, body: bytes) -> None:
        self.state.body = body
        self.body_event.set()

    def on_message_complete(self) -> None:
        if self.state.body is None:
            self.state.body = b""
        self.state.more_body = False
        self.body_event.set()

    def has_body(self) -> bool:
        return self.body_event.is_set() and self.state.body is not None

    def get_body(self) -> bytes:
        self.body_event.clear()
        body = self.state.body
        self.state.body = None
        assert body is not None
        return body

    def is_metadata_ready(self) -> bool:
        return self.state.is_metadata_ready()

    def get_metadata(self) -> RequestMetadata:
        return self.state.get_metadata()

    def is_keepalive(self) -> bool:
        return self.state.is_keepalive()

    def is_more_body(self) -> bool:
        return self.state.more_body

    def feed_data(self, data: bytes) -> None:
        self.parser.feed_data(data)
