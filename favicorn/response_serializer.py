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
        message = (
            f"HTTP/{http_version} {status}\n".encode()
            + self.encode_headers(headers)
        )
        if more_headers is False:
            message += b"\n"
        self.transport.write(message)

    def send_extra_headers(
        self,
        headers: Iterable[tuple[bytes, bytes]],
        more_headers: bool,
    ) -> None:
        message = self.encode_headers(headers)
        if more_headers is False:
            message += b"\n"
        self.transport.write(message)

    def send_body(
        self,
        body: bytes,
        more_body: bool,
    ) -> None:
        self.transport.write(body)
        if more_body is False:
            self.transport.write_eof()

    def close(self) -> None:
        self.transport.write_eof()

    def encode_headers(self, headers: Iterable[tuple[bytes, bytes]]) -> bytes:
        return b"".join(map(lambda h: h[0] + b": " + h[1] + b"\n", headers))
