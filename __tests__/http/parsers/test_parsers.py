from favicorn.connections.http.iparser import IHTTPParserFactory

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
    parser.feed_data(t_request.request_bytes)
    assert parser.is_metadata_ready()
    metadata = parser.get_metadata()
    assert_metadata_equals(metadata, t_request.expected_metadata)
    assert parser.has_body()
    assert parser.get_body() == t_request.expected_body
    assert parser.is_more_body() is False
