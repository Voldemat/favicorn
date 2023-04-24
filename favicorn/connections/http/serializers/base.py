import itertools
import time
from email.utils import formatdate
from http import HTTPStatus
from typing import Iterable, Sequence

from ..iserializer import IHTTPSerializer, IHTTPSerializerFactory
from ..response_metadata import ResponseMetadata


class HTTPBaseSerializer(IHTTPSerializer):
    include_server: bool
    include_timestamp: bool
    include_status_text: bool
    default_headers: Sequence[tuple[bytes, bytes]]

    def __init__(
        self,
        include_server: bool = True,
        include_timestamp: bool = True,
        include_status_text: bool = True,
        default_headers: Sequence[tuple[bytes, bytes]] = [],
    ) -> None:
        self.include_server = include_server
        self.include_timestamp = include_timestamp
        self.include_status_text = include_status_text
        self.default_headers = default_headers

    def serialize_metadata(
        self,
        metadata: ResponseMetadata,
    ) -> bytes:
        return (
            self.build_first_line(metadata.status)
            + b"\r\n"
            + self.serialize_headers(
                itertools.chain(self.get_default_headers(), metadata.headers)
            )
            + b"\r\n"
        )

    def build_first_line(self, status_code: int) -> bytes:
        status_text = ""
        if self.include_status_text:
            status_text = " " + HTTPStatus(status_code).phrase
        return f"HTTP/1.1 {status_code}{status_text}".encode()

    def get_default_headers(self) -> Iterable[tuple[bytes, bytes]]:
        default_headers = list(self.default_headers)
        if self.include_server:
            default_headers.append((b"Server", b"favicorn"))
        if self.include_timestamp:
            default_headers.append(
                (b"Date", formatdate(time.time(), usegmt=True).encode())
            )
        return default_headers

    def serialize_body(self, body: bytes) -> bytes:
        return body

    def serialize_headers(
        self, headers: Iterable[tuple[bytes, bytes]]
    ) -> bytes:
        return b"".join(map(lambda h: h[0] + b": " + h[1] + b"\r\n", headers))


class HTTPBaseSerializerFactory(IHTTPSerializerFactory):
    def build(self) -> IHTTPSerializer:
        return HTTPBaseSerializer()
