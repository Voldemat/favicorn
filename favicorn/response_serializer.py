import asyncio
from typing import Iterable


class HTTPResponseSerializer:
    transport: asyncio.WriteTransport

    def __init__(self, transport: asyncio.WriteTransport) -> None:
        self.transport = transport

    def start(
        self,
        http_version: str,
        status: int,
        headers: Iterable[tuple[bytes, bytes]],
        more_headers: bool,
    ) -> None:
        message = self.build_first_line(
            http_version, status
        ) + self.encode_headers(headers)
        if more_headers is False:
            message += b"\n"
        self.write(message)

    @staticmethod
    def build_first_line(http_version: str, status: int) -> bytes:
        return f"HTTP/{http_version} {status}\n".encode()

    def send_at_once(
        self,
        http_version: str,
        status: int,
        headers: Iterable[tuple[bytes, bytes]],
        body: bytes,
    ) -> None:
        message = (
            self.build_first_line(http_version, status)
            + self.encode_headers(headers)
            + b"\n"
            + body
        )
        self.write(message)
        self.close()

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
            self.close()

    def close(self) -> None:
        self.transport.write_eof()

    def encode_headers(self, headers: Iterable[tuple[bytes, bytes]]) -> bytes:
        return b"".join(map(lambda h: h[0] + b": " + h[1] + b"\n", headers))
