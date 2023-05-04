from favicorn.controllers.http.iparser import (
    HTTPParsingException,
    IHTTPParserFactory,
)

import pytest

from __tests__.http.conftest import parser_factories

from .conftest import (
    TestRequest,
    assert_metadata_equals,
    test_requests,
)


@pytest.mark.parametrize("parser_factory", parser_factories)
@pytest.mark.parametrize("t_request", test_requests)
async def test_parse_request(
    parser_factory: IHTTPParserFactory,
    t_request: TestRequest,
) -> None:
    parser = parser_factory.build()
    assert not parser.is_metadata_ready()
    parser.feed_data(t_request.request_bytes)
    assert parser.get_error() is None
    assert parser.is_metadata_ready()
    metadata = parser.get_metadata()
    assert_metadata_equals(metadata, t_request.expected_metadata)
    assert parser.get_body() == t_request.expected_body
    assert parser.is_more_body() is False


@pytest.mark.parametrize("parser_factory", parser_factories)
@pytest.mark.parametrize("t_request", test_requests)
async def test_parse_request_in_two_batches(
    parser_factory: IHTTPParserFactory,
    t_request: TestRequest,
) -> None:
    parser = parser_factory.build()
    assert not parser.is_metadata_ready()
    metadata_bytes, body_bytes = t_request.request_bytes.split(b"\r\n\r\n")
    first_batch = metadata_bytes[:-5]
    second_batch = (
        metadata_bytes[len(metadata_bytes) - 5 :] + b"\r\n\r\n" + body_bytes
    )
    parser.feed_data(first_batch)
    assert parser.get_error() is None
    assert not parser.is_metadata_ready()
    assert parser.is_more_body()
    parser.feed_data(second_batch)
    assert parser.get_error() is None
    assert parser.is_metadata_ready()
    assert_metadata_equals(parser.get_metadata(), t_request.expected_metadata)
    assert parser.get_body() == t_request.expected_body
    assert not parser.is_more_body()


@pytest.mark.parametrize(
    "request_bytes,expected_error",
    [
        (
            b"GET / HTTP/1.1\r\n\r\n\r\n",
            "Host header is abscent",
        ),
        (b"GET / HTTP/1.0\r\n\r\n\r\n", None),
        (b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n", None),
        (
            b"GET / HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Host: 127.0.0.1\r\n\r\n",
            "Host have multiple entries",
        ),
    ],
)
@pytest.mark.parametrize("parser_factory", parser_factories)
async def test_raise_error_on_h11_request_with_invalid_host(
    parser_factory: IHTTPParserFactory,
    request_bytes: bytes,
    expected_error: str | None,
) -> None:
    parser = parser_factory.build()
    assert not parser.is_metadata_ready()
    parser.feed_data(request_bytes)
    if expected_error is not None:
        exception = parser.get_error()
        assert isinstance(exception, HTTPParsingException), exception
        assert str(exception) == expected_error, exception
    else:
        error = parser.get_error()
        assert error is None
        assert parser.is_metadata_ready()
        assert parser.get_body() == b""
