import asyncio

import httptools

from .request import RequestBuilder


class HTTPRequestParser:
    def __init__(self, transport: asyncio.Transport) -> None:
        self.parser = httptools.HttpRequestParser(self)
        self.transport = transport
        self.request_builder = RequestBuilder()

    def on_message_begin(self) -> None:
        print("on_message_begin")

    def on_url(self, url: bytes) -> None:
        self.request_builder.url(url.decode())

    def on_header(self, name: bytes, value: bytes) -> None:
        self.request_builder.add_header(name.decode(), value.decode())

    def on_headers_complete(self) -> None:
        self.request_builder.method(self.parser.get_method().decode().upper())

    def on_body(self, body: bytes) -> None:
        self.request_builder.body(body)

    def on_chunk_header(self) -> None:
        print("on_chunk_header")

    def feed_data(self, data: bytes) -> None:
        self.parser.feed_data(data)

    def on_message_complete(self) -> None:
        request = self.request_builder.build()
        print(request)
        self.transport.write(b"HTTP/1.1 200 OK\n\nHello World\n")
        self.transport.write_eof()
