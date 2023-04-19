from favicorn.connections.http.iparser import (
    HTTPParsingException,
    IHTTPParserFactory,
)

import pytest

from .conftest import (
    TestRequest,
    assert_metadata_equals,
    parser_factories,
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
    assert not parser.has_body()
    assert not parser.has_error()
    parser.feed_data(t_request.request_bytes)
    assert not parser.has_error(), parser.get_error()
    assert parser.is_metadata_ready()
    metadata = parser.get_metadata()
    assert_metadata_equals(metadata, t_request.expected_metadata)
    assert parser.has_body()
    assert parser.get_body() == t_request.expected_body
    assert parser.is_more_body() is False


@pytest.mark.parametrize(
    "request_bytes,expected_error",
    [
        (
            b"GET / HTTP/1.1\r\n\r\n\r\n",
            "Host header is abscent",
        ),
        (b"GET / HTTP/1.0\r\n\r\n\r\n", None),
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
    assert not parser.has_body()
    assert not parser.has_error()
    parser.feed_data(request_bytes)
    if expected_error is not None:
        assert parser.has_error()
        exception = parser.get_error()
        assert isinstance(exception, HTTPParsingException), exception
        assert str(exception) == expected_error, exception
    else:
        assert not parser.has_error()
        assert parser.is_metadata_ready()
