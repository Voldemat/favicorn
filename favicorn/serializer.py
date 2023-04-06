import itertools
from dataclasses import dataclass
from http import HTTPStatus
from typing import Iterable

from .utils import get_date_in_email_format


@dataclass
class ResponseMetadata:
    status: int
    headers: Iterable[tuple[bytes, bytes]]

    def add_extra_headers(
        self, headers: Iterable[tuple[bytes, bytes]]
    ) -> None:
        self.headers = itertools.chain(self.headers, headers)


class HTTPSerializer:
    def __init__(self) -> None:
        self.data = b""
        self.is_response_completed = False
        self.is_metadata_received = False

    def is_response_started(self) -> bool:
        return self.is_metadata_received

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
        self.is_metadata_received = True

    def add_data(self, data: bytes) -> None:
        self.data += data

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

    def feed_body(
        self,
        body: bytes,
        more_body: bool,
    ) -> None:
        self.add_data(body)
        if more_body is False:
            self.finish_response()

    def finish_response(self) -> None:
        self.is_response_completed = True

    def encode_headers(self, headers: Iterable[tuple[bytes, bytes]]) -> bytes:
        return b"".join(map(lambda h: h[0] + b": " + h[1] + b"\r\n", headers))
