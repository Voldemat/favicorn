import itertools
import time
from email.utils import formatdate
from http import HTTPStatus
from typing import Iterable

from ..iserializer import IHTTPSerializer
from ..response_metadata import ResponseMetadata


class BaseHTTPSerializer(IHTTPSerializer):
    def serialize_metadata(
        self,
        metadata: ResponseMetadata,
    ) -> bytes:
        return (
            self.build_first_line(metadata.status)
            + b"\r\n"
            + self.encode_headers(
                itertools.chain(self.get_default_headers(), metadata.headers)
            )
            + b"\r\n"
        )

    @staticmethod
    def build_first_line(status_code: int) -> bytes:
        status_text = HTTPStatus(status_code).phrase
        return f"HTTP/1.1 {status_code} {status_text}".encode()

    @staticmethod
    def get_default_headers() -> Iterable[tuple[bytes, bytes]]:
        return (
            (b"Date", formatdate(time.time(), usegmt=True).encode()),
            (b"Server", b"favicorn"),
        )

    def serialize_body(self, body: bytes) -> bytes:
        return body

    def encode_headers(self, headers: Iterable[tuple[bytes, bytes]]) -> bytes:
        return b"".join(map(lambda h: h[0] + b": " + h[1] + b"\r\n", headers))
