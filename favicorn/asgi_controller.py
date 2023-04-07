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

from .parser import RequestMetadata
from .serializer import ResponseMetadata


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


class ASGIController(AsyncGenerator[dict[str, Any], None]):
    app: ASGI3Application
    events: Events
    queue: deque[dict[str, Any]]
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
        root_path: str,
        client: tuple[str, int] | None,
        server: tuple[str, int] | None,
    ) -> None:
        self.root_path = root_path
        self.server = server
        self.client = client
        self.app = app
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

    def is_started(self) -> bool:
        return self.task is not None

    def start(self, metadata: RequestMetadata) -> ASGIController:
        scope = HTTPScope(
            type="http",
            scheme="http",
            path=metadata.path,
            asgi=ASGIVersions(spec_version="2.3", version="3.0"),
            http_version=metadata.http_version,
            raw_path=metadata.raw_path,
            query_string=metadata.query_string,
            headers=metadata.headers,
            root_path=self.root_path,
            server=self.server,
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

    def __aiter__(self) -> AsyncGenerator[dict[str, Any], None]:
        return self

    async def asend(self, _: dict[str, Any] | None) -> dict[str, Any]:
        event = await self.get_event()
        if event is None:
            raise StopAsyncIteration()
        return event

    async def athrow(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await super().athrow(*args, **kwargs)

    async def get_event(self) -> dict[str, Any] | None:
        assert self.task is not None, "Application didn`t started yet"
        await self.events.new.wait()
        if len(self.queue) != 0:
            return self.queue.popleft()
        self.events.new.clear()
        if self.task.done():
            return None
        return await self.get_event()

    def dispatch_event(self, event: Any) -> None:
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
        self.dispatch_event({"type": "receive"})
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
            {
                "type": "send-metadata",
                "metadata": ResponseMetadata(
                    status=500,
                    headers=headers,
                ),
            }
        )
        self.dispatch_event(
            {
                "type": "send-body",
                "body": content,
                "more_body": False,
            }
        )

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
                        {
                            "type": "send-metadata",
                            "metadata": self.response_metadata,
                        }
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
                        {
                            "type": "send-metadata",
                            "metadata": self.response_metadata,
                        }
                    )
            case HTTPResponseEvents.BODY:
                event = cast(HTTPResponseBodyEvent, event)
                more_body = event.get("more_body", False)
                self.dispatch_event(
                    {
                        "type": "send-body",
                        "body": event["body"],
                        "more_body": more_body,
                    }
                )
                if more_body is False:
                    self.expected_event = None
            case _:
                raise RuntimeError(f"Unhandled event type: {event['type']}")

    def get_body(self) -> tuple[bytes, bool]:
        body = self.response_body
        assert body is not None
        self.response_body = b""
        return body, self.response_more_body

    def validate_event_type(self, event_type: str) -> None:
        assert self.expected_event is not None, "Response already ended"
        assert event_type == self.expected_event.value
