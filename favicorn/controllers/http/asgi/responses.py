from dataclasses import dataclass

from favicorn.controllers.http.response_metadata import ResponseMetadata


@dataclass
class PredefinedResponse:
    metadata: ResponseMetadata
    body: bytes


RESPONSE_CONTENT_400 = b"Invalid http request"
RESPONSE_400 = PredefinedResponse(
    metadata=ResponseMetadata(
        status=400,
        headers=(
            (b"Content-Type", b"text/plain; charset=utf-8"),
            (b"Content-Length", str(len(RESPONSE_CONTENT_400)).encode()),
        ),
    ),
    body=RESPONSE_CONTENT_400,
)

RESPONSE_CONTENT_500 = b"Internal Server Error"
RESPONSE_500 = PredefinedResponse(
    metadata=ResponseMetadata(
        status=500,
        headers=(
            (b"Content-Type", b"text/plain; charset=utf-8"),
            (b"Content-Length", str(len(RESPONSE_CONTENT_500)).encode()),
        ),
    ),
    body=RESPONSE_CONTENT_500,
)

RESPONSE_CONTENT_WEBSOCKETS_IS_NOT_SUPPORTED = (
    b"Websockets protocol is not supported"
)
RESPONSE_WEBSOCKETS_IS_NOT_SUPPORTED = PredefinedResponse(
    metadata=ResponseMetadata(
        status=400,
        headers=(
            (b"Content-Type", b"text/plain; charset=utf-8"),
            (
                b"Content-Length",
                str(
                    len(RESPONSE_CONTENT_WEBSOCKETS_IS_NOT_SUPPORTED)
                ).encode(),
            ),
        ),
    ),
    body=RESPONSE_CONTENT_WEBSOCKETS_IS_NOT_SUPPORTED,
)
