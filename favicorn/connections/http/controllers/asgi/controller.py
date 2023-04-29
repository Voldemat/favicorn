from __future__ import annotations

import asyncio
import enum
import logging
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from asgiref.typing import (
        ASGI3Application,
        ASGIReceiveEvent,
        ASGISendEvent,
        HTTPResponseBodyEvent,
        HTTPResponseStartEvent,
        HTTPResponseTrailersEvent,
        HTTPScope,
    )

from favicorn.connections.http.icontroller import IHTTPController
from favicorn.connections.http.ievent_bus import IHTTPEventBus
from favicorn.connections.http.iparser import HTTPParsingException, IHTTPParser
from favicorn.connections.http.iserializer import IHTTPSerializer
from favicorn.connections.http.request_metadata import RequestMetadata
from favicorn.connections.http.response_metadata import ResponseMetadata

from .scope_builder import ASGIScopeBuilder


class ASGIResponseEvents(enum.Enum):
    START = "http.response.start"
    TRAILERS = "http.response.trailers"
    BODY = "http.response.body"


class HTTPASGIController(IHTTPController):
    app: "ASGI3Application"
    task: asyncio.Task[None] | None
    response_metadata: ResponseMetadata | None
    expected_event: ASGIResponseEvents | None
    parser: IHTTPParser
    event_bus: IHTTPEventBus
    serializer: IHTTPSerializer
    logger: logging.Logger
    request_path: str | None

    def __init__(
        self,
        app: "ASGI3Application",
        parser: IHTTPParser,
        serializer: IHTTPSerializer,
        event_bus: IHTTPEventBus,
        logger: logging.Logger,
    ) -> None:
        self.app = app
        self.parser = parser
        self.logger = logger
        self.event_bus = event_bus
        self.serializer = serializer
        self.request_path = None

        self.task = None
        self.response_metadata = None
        self.expected_event = ASGIResponseEvents.START
        self.scope_builder = ASGIScopeBuilder()

    async def start(self, client: tuple[str, int] | None) -> IHTTPEventBus:
        self.task = asyncio.create_task(self.main(client))
        return self.event_bus

    async def main(self, client: tuple[str, int] | None) -> None:
        try:
            scope = await self.build_asgi_scope(client)
            if scope is None:
                await self.send_400_response()
                return
            await self.app(scope, self.receive, self.send)
        except BaseException:
            self.logger.exception("ASGICallable raised an exception")
            await self.send_500_response()

    async def build_asgi_scope(
        self, client: tuple[str, int] | None
    ) -> "HTTPScope" | None:
        metadata: RequestMetadata | None = None
        try:
            metadata = await self.wait_for_metadata()
        except HTTPParsingException:
            self.logger.exception(
                "ASGIController couldn`t obtain RequestMetadata"
            )
        if metadata is not None:
            self.logger.debug(f"ASGIController receives metadata: {metadata}")
            self.request_path = metadata.path
            scope = self.scope_builder.build(metadata, client)
            self.logger.debug(f"ASGIController builds scope: {scope}")
            return scope
        else:
            self.logger.error(
                "ASGIApplication couldn`t obtain RequestMetadata"
            )
            self.event_bus.close()
            return None

    async def wait_for_metadata(self) -> RequestMetadata | None:
        while not self.parser.is_metadata_ready():
            data = await self.event_bus.receive()
            if data is None:
                return None
            self.parser.feed_data(data)
            if exc := self.parser.get_error():
                raise exc
        return self.parser.get_metadata()

    async def stop(self) -> None:
        if self.task is None or self.task.done():
            return
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass

    async def receive(self) -> "ASGIReceiveEvent":
        data = self.parser.get_body()
        if data is None:
            if s_data := await self.event_bus.receive():
                self.parser.feed_data(s_data)
        data = self.parser.get_body()
        if data is None:
            return {"type": "http.disconnect"}
        return {
            "type": "http.request",
            "body": data,
            "more_body": self.parser.is_more_body(),
        }

    async def send(self, event: ASGISendEvent) -> None:
        self.validate_event_type(event["type"])
        match ASGIResponseEvents(event["type"]):
            case ASGIResponseEvents.START:
                event = cast("HTTPResponseStartEvent", event)
                self.response_metadata = ResponseMetadata(
                    status=event["status"],
                    headers=event["headers"],
                )
                if event.get("trailers", False) is True:
                    self.expected_event = ASGIResponseEvents.TRAILERS
                else:
                    self.expected_event = ASGIResponseEvents.BODY
                    self.event_bus.send(
                        self.serializer.serialize_metadata(
                            self.response_metadata
                        ),
                    )
                self.log_response(event["status"])
            case ASGIResponseEvents.TRAILERS:
                assert self.response_metadata is not None
                event = cast("HTTPResponseTrailersEvent", event)
                self.response_metadata.add_extra_headers(event["headers"])
                if event.get("more_trailers", False) is False:
                    self.expected_event = ASGIResponseEvents.BODY
                    self.event_bus.send(
                        self.serializer.serialize_metadata(
                            self.response_metadata
                        ),
                    )
            case ASGIResponseEvents.BODY:
                event = cast("HTTPResponseBodyEvent", event)
                self.event_bus.send(
                    self.serializer.serialize_body(event["body"])
                )
                if event.get("more_body", False) is False:
                    self.expected_event = None
                    self.event_bus.close()
            case _:
                raise RuntimeError(f"Unhandled event type: {event['type']}")

    def log_response(self, status: int) -> None:
        self.logger.info(f"[{status}] - {self.request_path}")

    async def send_400_response(self) -> None:
        content = b"Invalid http request"
        data = self.serializer.serialize_metadata(
            ResponseMetadata(
                status=400,
                headers=(
                    (b"Content-Type", b"text/plain; charset=utf-8"),
                    (b"Content-Length", str(len(content)).encode()),
                ),
            )
        ) + self.serializer.serialize_body(content)
        self.log_response(400)
        self.event_bus.send(data)
        self.event_bus.close()

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
        self.log_response(500)
        self.event_bus.send(data)
        self.event_bus.close()

    def validate_event_type(self, event_type: str) -> None:
        assert self.expected_event is not None, "Response already ended"
        assert (
            event_type == self.expected_event.value
        ), f"Unexpected event {event_type}"

    def is_keepalive(self) -> bool:
        return self.parser.is_keepalive()
