from __future__ import annotations

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
        Scope,
    )

from favicorn.i.event_bus import IEventBus
from favicorn.i.http.parser import IHTTPParser
from favicorn.i.http.request_metadata import RequestMetadata
from favicorn.i.http.response_metadata import ResponseMetadata
from favicorn.i.http.serializer import IHTTPSerializer

from .responses import PredefinedResponse, RESPONSE_400, RESPONSE_500
from .scope_builder import ASGIScopeBuilder


class ASGIEventManager:
    expected_event: str | None
    _scope: "Scope" | None

    def __init__(
        self,
        app: "ASGI3Application",
        http_parser: IHTTPParser,
        event_bus: IEventBus,
        http_serializer: IHTTPSerializer,
        logger: logging.Logger,
    ) -> None:
        self.app = app
        self.logger = logger
        self._scope = None
        self.expected_event = None
        self.event_bus = event_bus
        self.http_parser = http_parser
        self.http_serializer = http_serializer
        self.scope_builder = ASGIScopeBuilder()
        self._is_keepalive = False

    @property
    def scope(self) -> "Scope":
        assert self._scope is not None
        return self._scope

    async def launch_app(
        self, metadata: RequestMetadata | None, client: tuple[str, int] | None
    ) -> None:
        if metadata is None:
            self.send_predefined_response(RESPONSE_400)
            return
        self._is_keepalive = metadata.is_keepalive()
        self._scope = self.scope_builder.build(metadata, client)
        if self.scope["type"] == "http":
            self.expected_event = "http.response.start"
        else:
            self.expected_event = "websocket.accept"
        try:
            await self.app(self.scope, self.receive, self.send)
        except BaseException:
            self.logger.exception("ASGICallable raised an exception")
            self.send_predefined_response(RESPONSE_500)

    def send_predefined_response(self, response: PredefinedResponse) -> None:
        data = self.http_serializer.serialize_metadata(
            response.metadata
        ) + self.http_serializer.serialize_body(response.body)
        self.log_response(response.metadata.status)
        self.event_bus.send(data)

    def log_response(self, status: int) -> None:
        path = (
            self._scope.get("path", None) if self._scope is not None else None
        )
        self.logger.info(f"[{status}] - {path}")

    async def receive(self) -> "ASGIReceiveEvent":
        if self.scope["type"] == "http":
            return await self.receive_http()
        else:
            return await self.receive_websocket()

    async def receive_http(self) -> "ASGIReceiveEvent":
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

    async def receive_websocket(self) -> "ASGIReceiveEvent":
        return {
            "type": "websocket.receive",
            "bytes": b"",
            "text": None,
        }

    async def send(self, event: "ASGISendEvent") -> None:
        self.validate_event_type(event["type"])
        if self.scope["type"] == "http":
            await self.send_http(event)
        else:
            await self.send_websocket(event)

    async def send_http(
        self,
        event: "ASGISendEvent",
    ) -> None:
        match event["type"]:
            case "http.response.start":
                event = cast("HTTPResponseStartEvent", event)
                self.response_metadata = ResponseMetadata(
                    status=event["status"],
                    headers=event["headers"],
                )
                if event.get("trailers", False) is True:
                    self.expected_event = "http.response.trailers"
                else:
                    self.expected_event = "http.response.body"
                    self.event_bus.send(
                        self.http_serializer.serialize_metadata(
                            self.response_metadata
                        ),
                    )
            case "http.response.trailers":
                assert self.response_metadata is not None
                event = cast("HTTPResponseTrailersEvent", event)
                self.response_metadata.add_extra_headers(event["headers"])
                if event.get("more_trailers", False) is False:
                    self.expected_event = "http.response.body"
                    self.event_bus.send(
                        self.http_serializer.serialize_metadata(
                            self.response_metadata
                        ),
                    )
            case "http.response.body":
                event = cast("HTTPResponseBodyEvent", event)
                self.event_bus.send(
                    self.http_serializer.serialize_body(event["body"])
                )
                if event.get("more_body", False) is False:
                    self.expected_event = None
            case _:
                raise RuntimeError(f"Unhandled event type: {event['type']}")

    async def send_websocket(self, event: "ASGISendEvent") -> None:
        pass

    def validate_event_type(self, event_type: str) -> str:
        assert self.expected_event is not None, "No events was expected"
        assert (
            event_type == self.expected_event
        ), f"Unexpected event {event_type}"
        return event_type

    def is_keepalive(self) -> bool:
        return self._is_keepalive
