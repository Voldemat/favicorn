import asyncio
import itertools
from http import HTTPStatus
from typing import Iterable

from .utils import get_date_in_email_format


class HTTPResponseSerializer:
    transport: asyncio.WriteTransport
    keepalive: bool = False

    def __init__(self, transport: asyncio.WriteTransport) -> None:
        self.transport = transport
        self.keepalive = True

    def start(
        self,
        status: int,
        headers: Iterable[tuple[bytes, bytes]],
        more_headers: bool,
    ) -> None:
        message = self.build_first_line(status) + self.encode_headers(
            itertools.chain(self.get_default_headers(), headers)
        )
        if more_headers is False:
            message += b"\n"
        self.write(message)

    @staticmethod
    def build_first_line(status_code: int) -> bytes:
        status_text = HTTPStatus(status_code).phrase
        return f"HTTP/1.1 {status_code} {status_text}\n".encode()

    @staticmethod
    def get_default_headers() -> Iterable[tuple[bytes, bytes]]:
        return (
            (b"Date", get_date_in_email_format().encode()),
            (b"Server", b"favicorn"),
        )

    def send_at_once(
        self,
        status: int,
        headers: Iterable[tuple[bytes, bytes]],
        body: bytes,
    ) -> None:
        message = (
            self.build_first_line(status)
            + self.encode_headers(headers)
            + b"\n"
            + body
        )
        self.write(message)
        self.finish_response()

    def send_extra_headers(
        self,
        headers: Iterable[tuple[bytes, bytes]],
        more_headers: bool,
    ) -> None:
        message = self.encode_headers(headers)
        if more_headers is False:
            message += b"\n"
        self.write(message)

    def write(self, data: bytes) -> None:
        if self.transport.is_closing() is False:
            self.transport.write(data)

    def send_body(
        self,
        body: bytes,
        more_body: bool,
    ) -> None:
        self.write(body)
        if more_body is False:
            self.finish_response()

    def finish_response(self) -> None:
        if self.keepalive is False:
            self.transport.write_eof()

    def encode_headers(self, headers: Iterable[tuple[bytes, bytes]]) -> bytes:
        return b"".join(map(lambda h: h[0] + b": " + h[1] + b"\n", headers))
