import itertools
import time
from dataclasses import dataclass
from email.utils import formatdate
from http import HTTPStatus
from typing import Iterable


@dataclass
class ResponseMetadata:
    status: int
    headers: Iterable[tuple[bytes, bytes]]

    def add_extra_headers(
        self, headers: Iterable[tuple[bytes, bytes]]
    ) -> None:
        self.headers = itertools.chain(self.headers, headers)


class HTTPSerializer:
    data: bytes

    def __init__(self) -> None:
        self.data = b""

    def get_data(self) -> bytes:
        data = self.data
        self.data = b""
        return data

    def receive_metadata(
        self,
        metadata: ResponseMetadata,
    ) -> None:
        message = (
            self.build_first_line(metadata.status)
            + self.encode_headers(
                itertools.chain(self.get_default_headers(), metadata.headers)
            )
            + b"\r\n"
        )
        self.add_data(message)

    def add_data(self, data: bytes) -> None:
        self.data += data

    @staticmethod
    def build_first_line(status_code: int) -> bytes:
        status_text = HTTPStatus(status_code).phrase
        return f"HTTP/1.1 {status_code} {status_text}\n".encode()

    @staticmethod
    def get_default_headers() -> Iterable[tuple[bytes, bytes]]:
        return (
            (b"Date", formatdate(time.time(), usegmt=True).encode()),
            (b"Server", b"favicorn"),
        )

    def feed_body(self, body: bytes) -> None:
        self.add_data(body)

    def encode_headers(self, headers: Iterable[tuple[bytes, bytes]]) -> bytes:
        return b"".join(map(lambda h: h[0] + b": " + h[1] + b"\r\n", headers))
