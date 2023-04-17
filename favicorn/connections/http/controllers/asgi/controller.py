from __future__ import annotations

import asyncio
import enum
from typing import Any, cast

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

from favicorn.connections.http.controller_events import (
    HTTPControllerReceiveEvent,
    HTTPControllerSendEvent,
)
from favicorn.connections.http.icontroller import IHTTPController
from favicorn.connections.http.ievent_bus import IEventBus
from favicorn.connections.http.iparser import IHTTPParser
from favicorn.connections.http.iserializer import IHTTPSerializer
from favicorn.connections.http.request_metadata import RequestMetadata
from favicorn.connections.http.response_metadata import ResponseMetadata


class ASGIResponseEvents(enum.Enum):
    START = "http.response.start"
    TRAILERS = "http.response.trailers"
    BODY = "http.response.body"


class Events:
    receive: asyncio.Event
    send: asyncio.Event

    def __init__(self) -> None:
        self.receive = asyncio.Event()
        self.send = asyncio.Event()


class HTTPASGIController(IHTTPController):
    app: ASGI3Application
    events: Events
    task: asyncio.Task[Any] | None
    receive_buffer: bytes | None
    more_body: bool
    response_metadata: ResponseMetadata | None
    expected_event: ASGIResponseEvents | None
    response_body: bytes | None
    response_more_body: bool

    def __init__(
        self,
        app: ASGI3Application,
        parser: IHTTPParser,
        serializer: IHTTPSerializer,
        event_bus: IEventBus,
        client: tuple[str, int] | None,
    ) -> None:
        self.app = app
        self.parser = parser
        self.serializer = serializer
        self.client = client
        self.events = Events()
        self.task = None
        self.body = None
        self.receive_buffer = b""
        self.more_body = True
        self.expected_event = ASGIResponseEvents.START
        self.response_metadata = None
        self.more_headers = True
        self.response_body = None
        self.response_more_body = True
        self.event_bus = event_bus

    async def start(
        self,
        initial_data: bytes | None,
    ) -> IEventBus:
        if metadata := await self.wait_for_metadata(initial_data):
            scope = HTTPScope(
                type="http",
                scheme="http",
                path=metadata.path,
                asgi=ASGIVersions(spec_version="2.3", version="3.0"),
                http_version=metadata.http_version,
                raw_path=metadata.raw_path,
                query_string=metadata.query_string or b"",
                headers=metadata.headers,
                root_path="",
                server=None,
                client=self.client,
                extensions={},
                method=metadata.method,
            )
            self.task = asyncio.create_task(self.main(scope))
        else:
            self.event_bus.dispatch_event(None)
        return self.event_bus

    async def wait_for_metadata(
        self, initial_data: bytes | None
    ) -> RequestMetadata | None:
        if initial_data is not None:
            self.parser.feed_data(initial_data)
        while not self.parser.is_metadata_ready():
            data = await self.receive_from_connection()
            if data is None:
                return None
            self.parser.feed_data(data)
        return self.parser.get_metadata()

    async def receive_from_connection(self) -> bytes | None:
        self.event_bus.dispatch_event(HTTPControllerReceiveEvent())
        return await self.event_bus.receive()

    async def stop(self) -> None:
        if self.task is None or self.task.done():
            return
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass

    async def main(self, scope: HTTPScope) -> None:
        try:
            await self.app(scope, self.receive, self.send)
        except BaseException as unhandled_error:
            print("UnhandledError: ", unhandled_error.__repr__())
            await self.send_500_response()

    async def receive(self) -> ASGIReceiveEvent:
        if not self.parser.has_body():
            if data := await self.receive_from_connection():
                self.parser.feed_data(data)
        data = self.parser.get_body()
        if data is None:
            return HTTPDisconnectEvent(type="http.disconnect")
        return HTTPRequestEvent(
            type="http.request",
            body=data,
            more_body=self.parser.is_more_body(),
        )

    async def send_500_response(self) -> None:
        content = b"Internal Server Error"
        headers = (
            (b"Content-Type", b"text/plain; charset=utf-8"),
            (b"Content-Length", str(len(content)).encode()),
        )
        data = self.serializer.serialize_metadata(
            ResponseMetadata(
                status=500,
                headers=headers,
            )
        ) + self.serializer.serialize_body(content)
        self.event_bus.dispatch_event(HTTPControllerSendEvent(data))
        self.event_bus.dispatch_event(None)

    async def send(self, event: ASGISendEvent) -> None:
        self.validate_event_type(event["type"])
        match ASGIResponseEvents(event["type"]):
            case ASGIResponseEvents.START:
                event = cast(HTTPResponseStartEvent, event)
                self.response_metadata = ResponseMetadata(
                    status=event["status"],
                    headers=event["headers"],
                )
                trailers = event.get("trailers", False)
                if trailers is True:
                    self.expected_event = ASGIResponseEvents.TRAILERS
                else:
                    self.expected_event = ASGIResponseEvents.BODY
                    self.event_bus.dispatch_event(
                        HTTPControllerSendEvent(
                            self.serializer.serialize_metadata(
                                self.response_metadata
                            ),
                        )
                    )
            case ASGIResponseEvents.TRAILERS:
                assert (
                    self.response_metadata is not None
                ), "ResponseMetadata is not defined yet"
                event = cast(HTTPResponseTrailersEvent, event)
                more_trailers = event.get("more_trailers", False)
                self.response_metadata.add_extra_headers(event["headers"])
                if more_trailers is False:
                    self.expected_event = ASGIResponseEvents.BODY
                    self.event_bus.dispatch_event(
                        HTTPControllerSendEvent(
                            data=self.serializer.serialize_metadata(
                                self.response_metadata
                            ),
                        )
                    )
            case ASGIResponseEvents.BODY:
                event = cast(HTTPResponseBodyEvent, event)
                more_body = event.get("more_body", False)
                self.event_bus.dispatch_event(
                    HTTPControllerSendEvent(
                        self.serializer.serialize_body(event["body"])
                    )
                )
                if more_body is False:
                    self.expected_event = None
                    self.event_bus.dispatch_event(None)
            case _:
                raise RuntimeError(f"Unhandled event type: {event['type']}")

    def validate_event_type(self, event_type: str) -> None:
        assert self.expected_event is not None, "Response already ended"
        assert event_type == self.expected_event.value

    def is_keepalive(self) -> bool:
        return self.parser.is_keepalive()
