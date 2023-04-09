from favicorn.connections.http.parser import HTTPParser

import pytest


@pytest.fixture
def parser() -> HTTPParser:
    return HTTPParser()


async def test_parser(parser: HTTPParser) -> None:
    parser.feed_data(b"GET / HTTP/1.1\r\n\r\n\r\n")
    assert parser.state.is_metadata_ready()
    g_request = parser.state.get_metadata()
    assert g_request.method == "GET"
    assert g_request.path == "/"
    assert g_request.http_version == "1.1"
    g_body = parser.get_body()
    assert g_body == b""
    assert parser.state.more_body is False
    assert parser.state.is_keepalive() is True
    parser.feed_data(
        b"POST / HTTP/1.1\r\n"
        b"Connection: close\r\n"
        b"Content-Length: 12\r\n"
        b"Content-Type: application/x-www-form-urlencoded\r\n"
        b"\r\nHello World!\r\n"
    )
    p_request = parser.state.get_metadata()
    assert p_request.method == "POST"
    assert p_request.path == "/"
    assert p_request.http_version == "1.1"
    body = parser.get_body()
    assert body == b"Hello World!"
    assert parser.state.more_body is False


async def test_parser_with_h10(parser: HTTPParser) -> None:
    parser.feed_data(b"GET / HTTP/1.0\r\n\r\n\r\n")
    g_request = parser.state.get_metadata()
    assert g_request.method == "GET"
    assert g_request.path == "/"
    assert g_request.http_version == "1.0"
    assert parser.get_body() == b""
    assert parser.state.more_body is False
    assert parser.state.is_keepalive() is False
    parser = HTTPParser()
    parser.feed_data(
        b"POST / HTTP/1.0\r\n"
        b"Connection: Keep-Alive\r\n"
        b"Content-Length: 12\r\n"
        b"Content-Type: application/x-www-form-urlencoded\r\n"
        b"\r\nHello World!\r\n"
    )
    p_request = parser.state.get_metadata()
    assert p_request.method == "POST"
    assert p_request.path == "/"
    assert p_request.http_version == "1.0"
    assert parser.state.more_body is False
    assert parser.state.is_keepalive() is True
