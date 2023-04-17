from dataclasses import dataclass

from favicorn.connections.http.iparser import IHTTPParserFactory
from favicorn.connections.http.parsers import (
    H11HTTPParserFactory,
    HTTPToolsParserFactory,
)
from favicorn.connections.http.request_metadata import RequestMetadata

import h11

import httptools


parser_factories: list[IHTTPParserFactory] = [
    HTTPToolsParserFactory(httptools),
    H11HTTPParserFactory(h11),
]


@dataclass
class TestRequest:
    request_bytes: bytes
    expected_body: bytes
    expected_metadata: RequestMetadata

    __test__ = False


def assert_metadata_equals(
    metadata_1: RequestMetadata, metadata_2: RequestMetadata
) -> None:
    assert metadata_1.path == metadata_2.path
    assert metadata_1.method == metadata_2.method
    assert metadata_1.raw_path == metadata_2.raw_path
    assert metadata_1.http_version == metadata_2.http_version
    assert metadata_1.is_keepalive == metadata_2.is_keepalive
    assert metadata_1.query_string == metadata_2.query_string
    assert list(metadata_1.headers) == list(metadata_2.headers)


test_requests = [
    TestRequest(
        request_bytes=(
            b"GET / HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Accept: application/json\r\n\r\n"
        ),
        expected_metadata=RequestMetadata(
            path="/",
            method="GET",
            http_version="1.1",
            raw_path=b"/",
            query_string=None,
            is_keepalive=True,
            headers=(
                (b"host", b"localhost"),
                (b"accept", b"application/json"),
            ),
        ),
        expected_body=b"",
    ),
    TestRequest(
        request_bytes=(
            b"GET /animals/dogs/1?sortBy=createdAt HTTP/1.0\r\n"
            b"Accept:application/pdf\r\n\r\n"
        ),
        expected_metadata=RequestMetadata(
            path="/animals/dogs/1",
            method="GET",
            http_version="1.0",
            raw_path=b"/animals/dogs/1",
            query_string=b"sortBy=createdAt",
            is_keepalive=False,
            headers=((b"accept", b"application/pdf"),),
        ),
        expected_body=b"",
    ),
    TestRequest(
        request_bytes=(
            b"GET /pets/cats/2 HTTP/1.0\r\n" b"Connection: keep-alive\r\n\r\n"
        ),
        expected_metadata=RequestMetadata(
            path="/pets/cats/2",
            method="GET",
            http_version="1.0",
            raw_path=b"/pets/cats/2",
            query_string=None,
            is_keepalive=True,
            headers=((b"connection", b"keep-alive"),),
        ),
        expected_body=b"",
    ),
    TestRequest(
        request_bytes=(
            b"GET / HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Connection: close\r\n\r\n"
        ),
        expected_metadata=RequestMetadata(
            path="/",
            method="GET",
            http_version="1.1",
            raw_path=b"/",
            query_string=None,
            is_keepalive=False,
            headers=(
                (b"host", b"localhost"),
                (b"connection", b"close"),
            ),
        ),
        expected_body=b"",
    ),
    TestRequest(
        request_bytes=(
            b"POST /data/ HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Content-Length: 33\r\n"
            b"Content-Type: application/json\r\n\r\n"
            b'{"key": 1, "value": "great-city"}'
        ),
        expected_metadata=RequestMetadata(
            path="/data/",
            method="POST",
            http_version="1.1",
            raw_path=b"/data/",
            query_string=None,
            is_keepalive=True,
            headers=(
                (b"host", b"localhost"),
                (b"content-length", b"33"),
                (b"content-type", b"application/json"),
            ),
        ),
        expected_body=b'{"key": 1, "value": "great-city"}',
    ),
    TestRequest(
        request_bytes=(
            b"POST /data/ HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Content-Length: 33\r\n"
            b"Content-Type: application/json\r\n\r\n"
            b'{"key": 1, "value": "great-city"}'
        ),
        expected_metadata=RequestMetadata(
            path="/data/",
            method="POST",
            http_version="1.1",
            raw_path=b"/data/",
            query_string=None,
            is_keepalive=True,
            headers=(
                (b"host", b"localhost"),
                (b"content-length", b"33"),
                (b"content-type", b"application/json"),
            ),
        ),
        expected_body=b'{"key": 1, "value": "great-city"}',
    ),
]
