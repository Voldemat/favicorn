import time

from favicorn.i.protocols.http.serializer import IHTTPSerializerFactory

import pytest

from __tests__.factories import http_serializer_factories

from .conftest import TestResponse, test_responses


@pytest.mark.parametrize("serializer_factory", http_serializer_factories)
@pytest.mark.parametrize("t_response", test_responses)
async def test_serialize_response(
    serializer_factory: IHTTPSerializerFactory,
    t_response: TestResponse,
) -> None:
    timestamp = time.time()
    serializer = serializer_factory.build()
    assert t_response.expected_metadata_bytes(
        timestamp
    ) == serializer.serialize_metadata(t_response.metadata)
    assert t_response.expected_body_bytes == serializer.serialize_body(
        t_response.body,
    )
