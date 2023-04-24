import time
from dataclasses import dataclass
from email.utils import formatdate

from favicorn.connections.http.response_metadata import ResponseMetadata


@dataclass
class TestResponse:
    body: bytes
    metadata: ResponseMetadata
    expected_body_bytes: bytes
    expected_metadata_bytes: bytes

    __test__ = False


def get_date() -> str:
    return formatdate(time.time(), usegmt=True)


test_responses = [
    TestResponse(
        metadata=ResponseMetadata(
            status=200,
            headers=[],
        ),
        expected_metadata_bytes=(
            b"HTTP/1.1 200 OK\r\n"
            b"Server: favicorn\r\n" + f"Date: {get_date()}\r\n\r\n".encode()
        ),
        body=b"",
        expected_body_bytes=b"",
    ),
    TestResponse(
        metadata=ResponseMetadata(
            status=400, headers=[(b"Content-Length", b"100")]
        ),
        expected_metadata_bytes=(
            b"HTTP/1.1 400 Bad Request\r\n"
            b"Server: favicorn\r\n"
            + f"Date: {get_date()}\r\n".encode()
            + b"Content-Length: 100\r\n\r\n"
        ),
        body=b"Hello world!",
        expected_body_bytes=b"Hello world!",
    ),
]
