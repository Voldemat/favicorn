import asyncio
import enum
from typing import Iterable, cast

from asgiref.typing import (
    ASGISendEvent,
    HTTPResponseBodyEvent,
    HTTPResponseStartEvent,
    HTTPResponseTrailersEvent,
)


class HTTPResponseEvents(enum.Enum):
    START = "http.response.start"
    TRAILERS = "http.response.trailers"
    BODY = "http.response.body"


class HTTPResponseSerializer:
    expected_event: HTTPResponseEvents | None
    transport: asyncio.WriteTransport

    def __init__(self, transport: asyncio.WriteTransport) -> None:
        self.expected_event = HTTPResponseEvents.START
        self.transport = transport

    def is_completed(self) -> bool:
        return self.expected_event is None

    def send(self, event: ASGISendEvent) -> None:
        self.validate_event(event)
        match event["type"]:
            case HTTPResponseEvents.START.value:
                event = cast(HTTPResponseStartEvent, event)
                headers = self.encode_headers(event["headers"])
                message: bytes = (
                    f'HTTP/1.1 {event["status"]}\n'.encode() + headers
                )
                if event.get("trailers", False) is True:
                    self.expected_event = HTTPResponseEvents.TRAILERS
                else:
                    self.expected_event = HTTPResponseEvents.BODY
                    message += b"\n"
                self.transport.write(message)
            case HTTPResponseEvents.TRAILERS.value:
                event = cast(HTTPResponseTrailersEvent, event)
                message = self.encode_headers(event["headers"])
                if event.get("more_trailers", False) is False:
                    message += b"\n"
                    self.expected_event = HTTPResponseEvents.BODY
                self.transport.write(message)
            case HTTPResponseEvents.BODY.value:
                event = cast(HTTPResponseBodyEvent, event)
                message = event["body"]
                self.transport.write(message)
                if event.get("more_body", False) is False:
                    self.expected_event = None
                    self.transport.write_eof()
            case _:
                self.transport.write_eof()
                raise RuntimeError(f"Unhandled event type: {event['type']}")

    def encode_headers(self, headers: Iterable[tuple[bytes, bytes]]) -> bytes:
        return b"".join(map(lambda h: h[0] + b": " + h[1] + b"\n", headers))

    def validate_event(self, event: ASGISendEvent) -> None:
        assert self.expected_event is not None, "Response already ended"
        assert event["type"] == self.expected_event.value
