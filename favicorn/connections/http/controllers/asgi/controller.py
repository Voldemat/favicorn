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
        WWWScope,
    )

from favicorn.connections.http.icontroller import IHTTPController
from favicorn.connections.http.ievent_bus import IHTTPEventBus
from favicorn.connections.http.iparser import IHTTPParser
from favicorn.connections.http.iserializer import IHTTPSerializer
from favicorn.connections.http.request_metadata import RequestMetadata
from favicorn.connections.http.response_metadata import ResponseMetadata

from .responses import (
    PredefinedResponse,
    RESPONSE_400,
    RESPONSE_500,
    RESPONSE_WEBSOCKETS_IS_NOT_SUPPORTED,
)
from .scope_builder import ASGIScopeBuilder


class ASGISendEventType(enum.Enum):
    HTTP_START = "http.response.start"
    HTTP_TRAILERS = "http.response.trailers"
    HTTP_BODY = "http.response.body"


class HTTPASGIController(IHTTPController):
    app: "ASGI3Application"
    task: asyncio.Task[None] | None
    response_metadata: ResponseMetadata | None
    expected_event: ASGISendEventType | None
    http_parser: IHTTPParser
    event_bus: IHTTPEventBus
    serializer: IHTTPSerializer
    logger: logging.Logger
    request_path: str | None
    scope: "WWWScope" | None

    def __init__(
        self,
        app: "ASGI3Application",
        http_parser: IHTTPParser,
        serializer: IHTTPSerializer,
        event_bus: IHTTPEventBus,
        logger: logging.Logger,
    ) -> None:
        self.app = app
        self.http_parser = http_parser
        self.logger = logger
        self.event_bus = event_bus
        self.serializer = serializer
        self.request_path = None
        self.scope = None

        self.task = None
        self.response_metadata = None
        self.expected_event = None
        self.scope_builder = ASGIScopeBuilder()

    async def start(self, client: tuple[str, int] | None) -> None:
        self.task = asyncio.create_task(self.main(client))

    async def main(self, client: tuple[str, int] | None) -> None:
        try:
            result = await self.build_asgi_scope(client)
            if result[0] is None:
                self.send_predefined_response(result[1])
            else:
                self.scope = result[0]
                await self.app(result[0], self.receive, self.send)
        except BaseException:
            self.logger.exception("ASGICallable raised an exception")
            self.send_predefined_response(RESPONSE_500)
        finally:
            self.event_bus.close()

    async def build_asgi_scope(
        self, client: tuple[str, int] | None
    ) -> tuple["WWWScope", None] | tuple[None, PredefinedResponse]:
        metadata = await self.wait_for_metadata()
        if metadata is None:
            return (None, RESPONSE_400)
        self.logger.debug(f"ASGIController receives metadata: {metadata}")
        self.request_path = metadata.path
        scope = self.scope_builder.build(metadata, client)
        if scope["type"] == "http":
            self.expected_event = ASGISendEventType.HTTP_START
        else:
            return (None, RESPONSE_WEBSOCKETS_IS_NOT_SUPPORTED)
        self.logger.debug(f"ASGIController builds scope: {scope}")
        return (scope, None)

    async def wait_for_metadata(self) -> RequestMetadata | None:
        while not self.http_parser.is_metadata_ready():
            data = await self.event_bus.receive()
            if data is None:
                return None
            self.http_parser.feed_data(data)
            if exc := self.http_parser.get_error():
                self.logger.error(exc, exc_info=True)
                return None
        return self.http_parser.get_metadata()

    async def stop(self) -> None:
        if self.task is None or self.task.done():
            return
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass

    async def receive(self) -> "ASGIReceiveEvent":
        data = self.http_parser.get_body()
        if data is None:
            if s_data := await self.event_bus.receive():
                self.http_parser.feed_data(s_data)
        data = self.http_parser.get_body()
        if data is None:
            return {"type": "http.disconnect"}
        return {
            "type": "http.request",
            "body": data,
            "more_body": self.http_parser.is_more_body(),
        }

    async def send(self, event: ASGISendEvent) -> None:
        match self.build_send_event_type(event["type"]):
            case ASGISendEventType.HTTP_START:
                event = cast("HTTPResponseStartEvent", event)
                self.response_metadata = ResponseMetadata(
                    status=event["status"],
                    headers=event["headers"],
                )
                if event.get("trailers", False) is True:
                    self.expected_event = ASGISendEventType.HTTP_TRAILERS
                else:
                    self.expected_event = ASGISendEventType.HTTP_BODY
                    self.event_bus.send(
                        self.serializer.serialize_metadata(
                            self.response_metadata
                        ),
                    )
                self.log_response(event["status"])
            case ASGISendEventType.HTTP_TRAILERS:
                assert self.response_metadata is not None
                event = cast("HTTPResponseTrailersEvent", event)
                self.response_metadata.add_extra_headers(event["headers"])
                if event.get("more_trailers", False) is False:
                    self.expected_event = ASGISendEventType.HTTP_BODY
                    self.event_bus.send(
                        self.serializer.serialize_metadata(
                            self.response_metadata
                        ),
                    )
            case ASGISendEventType.HTTP_BODY:
                event = cast("HTTPResponseBodyEvent", event)
                self.event_bus.send(
                    self.serializer.serialize_body(event["body"])
                )
                if event.get("more_body", False) is False:
                    self.expected_event = None
            case _:
                raise RuntimeError(f"Unhandled event type: {event['type']}")

    def log_response(self, status: int) -> None:
        self.logger.info(f"[{status}] - {self.request_path}")

    def send_predefined_response(self, response: PredefinedResponse) -> None:
        data = self.serializer.serialize_metadata(
            response.metadata
        ) + self.serializer.serialize_body(response.body)
        self.log_response(response.metadata.status)
        self.event_bus.send(data)

    def build_send_event_type(self, event_type: str) -> ASGISendEventType:
        assert self.expected_event is not None, "No events was expected"
        assert (
            event_type == self.expected_event.value
        ), f"Unexpected event {event_type}"
        return ASGISendEventType(event_type)

    def is_keepalive(self) -> bool:
        return self.http_parser.is_keepalive()
