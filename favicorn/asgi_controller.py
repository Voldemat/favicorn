import enum
from typing import Iterable, cast

from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveEvent,
    ASGISendEvent,
    ASGIVersions,
    HTTPDisconnectEvent,
    HTTPRequestEvent,
    HTTPResponseBodyEvent,
    HTTPResponseStartEvent,
    HTTPResponseTrailersEvent,
    HTTPScope,
)

from .request_parser import HTTPRequestParser
from .response_serializer import HTTPResponseSerializer


class HTTPResponseEvents(enum.Enum):
    START = "http.response.start"
    TRAILERS = "http.response.trailers"
    BODY = "http.response.body"


class ASGIController:
    app: ASGI3Application
    request_parser: HTTPRequestParser
    response_serializer: HTTPResponseSerializer
    expected_event: HTTPResponseEvents | None

    def __init__(
        self,
        app: ASGI3Application,
        request_parser: HTTPRequestParser,
        response_serializer: HTTPResponseSerializer,
    ) -> None:
        self.app = app
        self.request_parser = request_parser
        self.response_serializer = response_serializer
        self.expected_event = HTTPResponseEvents.START

    async def start(self) -> None:
        request = await self.request_parser.get_request()
        scope = HTTPScope(
            type="http",
            asgi=ASGIVersions(spec_version="2.3", version="3.0"),
            http_version=request.http_version,
            scheme=request.scheme,
            path=request.path,
            raw_path=request.raw_path,
            query_string=request.query_string,
            root_path=request.root_path,
            headers=request.headers,
            server=request.server,
            client=request.client,
            extensions={},
            method=request.method,
        )
        try:
            await self.app(scope, self.receive, self.send)
        except BaseException as unhandled_error:
            print(unhandled_error)
            await self.send_500_response()

    async def receive(self) -> ASGIReceiveEvent:
        body, more_body = await self.request_parser.receive_body()
        if body is None:
            return HTTPDisconnectEvent(type="http.disconnect")
        return HTTPRequestEvent(
            type="http.request",
            body=body,
            more_body=more_body,
        )

    async def send_500_response(self) -> None:
        content = b"Internal Server Error"
        headers = (
            (b"Content-Type", b"text/plain; charset=utf-8"),
            (b"Content-Length", str(len(content)).encode()),
        )
        self.response_serializer.send_at_once(
            http_version="1.1",
            status=500,
            headers=headers,
            body=content,
        )

    async def send(self, event: ASGISendEvent) -> None:
        self.validate_event_type(event["type"])
        match event["type"]:
            case HTTPResponseEvents.START.value:
                event = cast(HTTPResponseStartEvent, event)
                trailers = event.get("trailers", False)
                if trailers is True:
                    self.expected_event = HTTPResponseEvents.TRAILERS
                else:
                    self.expected_event = HTTPResponseEvents.BODY
                self.response_serializer.start(
                    http_version="1.1",
                    status=event["status"],
                    headers=event["headers"],
                    more_headers=trailers,
                )
            case HTTPResponseEvents.TRAILERS.value:
                event = cast(HTTPResponseTrailersEvent, event)
                more_trailers = event.get("more_trailers", False)
                if more_trailers is False:
                    self.expected_event = HTTPResponseEvents.BODY
                self.response_serializer.send_extra_headers(
                    event["headers"],
                    more_trailers,
                )
            case HTTPResponseEvents.BODY.value:
                event = cast(HTTPResponseBodyEvent, event)
                more_body = event.get("more_body", False)
                if more_body is False:
                    self.expected_event = None
                self.response_serializer.send_body(
                    body=event["body"],
                    more_body=more_body,
                )
            case _:
                self.response_serializer.close()
                raise RuntimeError(f"Unhandled event type: {event['type']}")

    def encode_headers(self, headers: Iterable[tuple[bytes, bytes]]) -> bytes:
        return b"".join(map(lambda h: h[0] + b": " + h[1] + b"\n", headers))

    def validate_event_type(self, event_type: str) -> None:
        assert self.expected_event is not None, "Response already ended"
        assert event_type == self.expected_event.value
