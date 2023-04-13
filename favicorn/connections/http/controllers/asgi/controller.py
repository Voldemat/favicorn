from __future__ import annotations

import asyncio
import enum
from collections import deque
from typing import Any, AsyncGenerator, cast

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

from favicorn.connections.http.icontroller import (
    HTTPControllerEvent,
    HTTPControllerReceiveEvent,
    HTTPControllerSendEvent,
    IHTTPController,
)
from favicorn.connections.http.iparser import IHTTPParser
from favicorn.connections.http.iserializer import IHTTPSerializer
from favicorn.connections.http.request_metadata import RequestMetadata
from favicorn.connections.http.response_metadata import ResponseMetadata


class HTTPResponseEvents(enum.Enum):
    START = "http.response.start"
    TRAILERS = "http.response.trailers"
    BODY = "http.response.body"


class Events:
    receive: asyncio.Event
    new: asyncio.Event

    def __init__(self) -> None:
        self.receive = asyncio.Event()
        self.new = asyncio.Event()


class HTTPASGIController(
    IHTTPController, AsyncGenerator[HTTPControllerEvent, None]
):
    app: ASGI3Application
    events: Events
    queue: deque[HTTPControllerEvent]
    task: asyncio.Task[Any] | None
    receive_buffer: bytes | None
    more_body: bool
    response_metadata: ResponseMetadata | None
    expected_event: HTTPResponseEvents | None
    response_body: bytes | None
    response_more_body: bool

    def __init__(
        self,
        app: ASGI3Application,
        parser: IHTTPParser,
        serializer: IHTTPSerializer,
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
        self.expected_event = HTTPResponseEvents.START
        self.response_metadata = None
        self.more_headers = True
        self.response_body = None
        self.response_more_body = True
        self.queue = deque()

    async def start(
        self,
        initial_data: bytes | None,
    ) -> AsyncGenerator[HTTPControllerEvent, None]:
        metadata = await self.wait_for_metadata(initial_data)
        if metadata is None:
            return self
        scope = HTTPScope(
            type="http",
            scheme="http",
            path=metadata.path,
            asgi=ASGIVersions(spec_version="2.3", version="3.0"),
            http_version=metadata.http_version,
            raw_path=metadata.raw_path,
            query_string=metadata.query_string,
            headers=metadata.headers,
            root_path="",
            server=None,
            client=self.client,
            extensions={},
            method=metadata.method,
        )
        self.task = asyncio.create_task(self.main(scope))
        return self

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
        self.dispatch_event(HTTPControllerReceiveEvent())
        await self.events.receive.wait()
        self.events.receive.clear()
        return self.receive_buffer

    async def stop(self) -> None:
        if self.task is None or self.task.done():
            return
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass

    def __aiter__(self) -> AsyncGenerator[HTTPControllerEvent, None]:
        return self

    async def asend(self, _: dict[str, Any] | None) -> HTTPControllerEvent:
        event = await self.get_event()
        if event is None:
            raise StopAsyncIteration()
        return event

    async def athrow(self, *args: Any, **kwargs: Any) -> HTTPControllerEvent:
        return await super().athrow(*args, **kwargs)

    async def get_event(self) -> HTTPControllerEvent | None:
        if self.task is None:
            return None
        await self.events.new.wait()
        if len(self.queue) != 0:
            return self.queue.popleft()
        self.events.new.clear()
        if self.task.done():
            return None
        return await self.get_event()

    def dispatch_event(self, event: HTTPControllerEvent) -> None:
        self.queue.append(event)
        self.events.new.set()

    async def main(self, scope: HTTPScope) -> None:
        try:
            await self.app(scope, self.receive, self.send)
        except BaseException as unhandled_error:
            print("UnhandledError: ", unhandled_error.__repr__())
            await self.send_500_response()

    def receive_data(self, data: bytes | None) -> None:
        self.receive_buffer = data
        self.events.receive.set()

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
        self.dispatch_event(HTTPControllerSendEvent(data))

    async def send(self, event: ASGISendEvent) -> None:
        self.validate_event_type(event["type"])
        match HTTPResponseEvents(event["type"]):
            case HTTPResponseEvents.START:
                event = cast(HTTPResponseStartEvent, event)
                self.response_metadata = ResponseMetadata(
                    status=event["status"],
                    headers=event["headers"],
                )
                trailers = event.get("trailers", False)
                if trailers is True:
                    self.expected_event = HTTPResponseEvents.TRAILERS
                else:
                    self.expected_event = HTTPResponseEvents.BODY
                    self.dispatch_event(
                        HTTPControllerSendEvent(
                            self.serializer.serialize_metadata(
                                self.response_metadata
                            ),
                        )
                    )
            case HTTPResponseEvents.TRAILERS:
                assert (
                    self.response_metadata is not None
                ), "ResponseMetadata is not defined yet"
                event = cast(HTTPResponseTrailersEvent, event)
                more_trailers = event.get("more_trailers", False)
                self.response_metadata.add_extra_headers(event["headers"])
                if more_trailers is False:
                    self.expected_event = HTTPResponseEvents.BODY
                    self.dispatch_event(
                        HTTPControllerSendEvent(
                            data=self.serializer.serialize_metadata(
                                self.response_metadata
                            ),
                        )
                    )
            case HTTPResponseEvents.BODY:
                event = cast(HTTPResponseBodyEvent, event)
                more_body = event.get("more_body", False)
                self.dispatch_event(
                    HTTPControllerSendEvent(
                        self.serializer.serialize_body(event["body"])
                    )
                )
                if more_body is False:
                    self.expected_event = None
            case _:
                raise RuntimeError(f"Unhandled event type: {event['type']}")

    def validate_event_type(self, event_type: str) -> None:
        assert self.expected_event is not None, "Response already ended"
        assert event_type == self.expected_event.value

    def is_keepalive(self) -> bool:
        return self.parser.is_keepalive()
