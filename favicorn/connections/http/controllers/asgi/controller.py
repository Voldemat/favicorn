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
    HTTPControllerSendBodyEvent,
    HTTPControllerSendMetadataEvent,
    IHTTPController,
)
from favicorn.connections.http.request_metadata import RequestMetadata
from favicorn.connections.http.response_metadata import ResponseMetadata


class HTTPResponseEvents(enum.Enum):
    START = "http.response.start"
    TRAILERS = "http.response.trailers"
    BODY = "http.response.body"


class Events:
    body: asyncio.Event
    new: asyncio.Event

    def __init__(self) -> None:
        self.body = asyncio.Event()
        self.new = asyncio.Event()


class HTTPASGIController(
    IHTTPController, AsyncGenerator[HTTPControllerEvent, None]
):
    app: ASGI3Application
    events: Events
    queue: deque[HTTPControllerEvent]
    task: asyncio.Task[Any] | None
    body: bytes | None
    more_body: bool
    response_metadata: ResponseMetadata | None
    expected_event: HTTPResponseEvents | None
    response_body: bytes | None
    response_more_body: bool

    def __init__(
        self,
        app: ASGI3Application,
        client: tuple[str, int] | None,
    ) -> None:
        self.app = app
        self.client = client
        self.events = Events()
        self.task = None
        self.body = None
        self.more_body = True
        self.expected_event = HTTPResponseEvents.START
        self.response_metadata = None
        self.more_headers = True
        self.response_body = None
        self.response_more_body = True
        self.queue = deque()

    def start(
        self,
        metadata: RequestMetadata,
    ) -> AsyncGenerator[HTTPControllerEvent, None]:
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
        assert self.task is not None, "Application didn`t started yet"
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

    def receive_body(self, body: bytes, more_body: bool) -> None:
        self.body = body
        self.more_body = more_body
        self.events.body.set()

    def disconnect(self) -> None:
        self.body = None
        self.more_body = False
        self.events.body.set()

    async def receive(self) -> ASGIReceiveEvent:
        self.dispatch_event(HTTPControllerReceiveEvent())
        await self.events.body.wait()
        self.events.body.clear()
        if self.body is None:
            return HTTPDisconnectEvent(type="http.disconnect")
        return HTTPRequestEvent(
            type="http.request",
            body=self.body,
            more_body=self.more_body,
        )

    async def send_500_response(self) -> None:
        content = b"Internal Server Error"
        headers = (
            (b"Content-Type", b"text/plain; charset=utf-8"),
            (b"Content-Length", str(len(content)).encode()),
        )
        self.dispatch_event(
            HTTPControllerSendMetadataEvent(
                metadata=ResponseMetadata(
                    status=500,
                    headers=headers,
                ),
            )
        )
        self.dispatch_event(HTTPControllerSendBodyEvent(body=content))

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
                        HTTPControllerSendMetadataEvent(
                            metadata=self.response_metadata,
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
                        HTTPControllerSendMetadataEvent(
                            metadata=self.response_metadata,
                        )
                    )
            case HTTPResponseEvents.BODY:
                event = cast(HTTPResponseBodyEvent, event)
                more_body = event.get("more_body", False)
                self.dispatch_event(
                    HTTPControllerSendBodyEvent(body=event["body"])
                )
                if more_body is False:
                    self.expected_event = None
            case _:
                raise RuntimeError(f"Unhandled event type: {event['type']}")

    def validate_event_type(self, event_type: str) -> None:
        assert self.expected_event is not None, "Response already ended"
        assert event_type == self.expected_event.value


class HTTPASGIControllerFactory:
    def build(
        self, app: ASGI3Application, client: tuple[str, int] | None
    ) -> HTTPASGIController:
        return HTTPASGIController(
            app=app,
            client=client,
        )
