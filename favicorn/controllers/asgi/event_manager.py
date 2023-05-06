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
        WebSocketAcceptEvent,
        Scope,
    )

from favicorn.i.event_bus import IEventBus
from favicorn.i.http.parser import IHTTPParser
from favicorn.i.http.request_metadata import RequestMetadata
from favicorn.i.http.response_metadata import ResponseMetadata
from favicorn.i.http.serializer import IHTTPSerializer
from favicorn.i.websocket.parser import IWebsocketParser
from favicorn.i.websocket.serializer import IWebsocketSerializer

from .responses import PredefinedResponse, RESPONSE_400, RESPONSE_500
from .scope_builder import ASGIScopeBuilder


class ASGIEventManager:
    expected_events: list[str]
    _scope: "Scope" | None

    def __init__(
        self,
        app: "ASGI3Application",
        event_bus: IEventBus,
        logger: logging.Logger,
        http_parser: IHTTPParser,
        http_serializer: IHTTPSerializer,
        websocket_parser: IWebsocketParser | None,
        websocket_serializer: IWebsocketSerializer | None,
    ) -> None:
        self.app = app
        self._scope = None
        self.logger = logger
        self.expected_events = []
        self._is_keepalive = False
        self.event_bus = event_bus
        self.http_parser = http_parser
        self.http_serializer = http_serializer
        self.scope_builder = ASGIScopeBuilder()
        self._websocket_parser = websocket_parser
        self._websocket_serializer = websocket_serializer

    @property
    def scope(self) -> "Scope":
        assert self._scope is not None
        return self._scope

    @property
    def websocket_parser(self) -> IWebsocketParser:
        assert self._websocket_parser is not None
        return self._websocket_parser

    @property
    def websocket_serializer(self) -> IWebsocketSerializer:
        assert self._websocket_serializer is not None
        return self._websocket_serializer

    async def launch_app(
        self, metadata: RequestMetadata | None, client: tuple[str, int] | None
    ) -> None:
        if metadata is None:
            self.send_predefined_response(RESPONSE_400)
            return
        self._is_keepalive = metadata.is_keepalive()
        self._scope = self.scope_builder.build(metadata, client)
        if self.scope["type"] == "http":
            self.expected_events = ["http.response.start"]
        else:
            self.expected_events = ["websocket.accept", "websocket.close"]
        try:
            await self.app(self.scope, self.receive, self.send)
            if not self.is_response_completed():
                raise RuntimeError(
                    "ASGICallable returns before finishing the response"
                )
        except BaseException:
            self.logger.exception("ASGICallable raised an exception")
            self.send_predefined_response(RESPONSE_500)

    def is_response_completed(self) -> bool:
        return len(self.expected_events) == 0

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
        if "websocket.send" not in self.expected_events:
            return {"type": "websocket.connect"}
        data = self.websocket_parser.get_data()
        if data is None:
            if s_data := await self.event_bus.receive():
                self.websocket_parser.feed_data(s_data)
            data = self.websocket_parser.get_data()
        if isinstance(data, int):
            return {
                "type": "websocket.disconnect",
                "code": data,
            }
        elif isinstance(data, str):
            return {
                "type": "websocket.receive",
                "bytes": None,
                "text": data,
            }
        elif isinstance(data, bytes):
            return {"type": "websocket.receive", "bytes": data, "text": None}
        else:
            raise ValueError(f"Unhandled data type: {type(data)}")

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
                    self.expected_events = ["http.response.trailers"]
                else:
                    self.expected_events = ["http.response.body"]
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
                    self.expected_events = ["http.response.body"]
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
                    self.expected_events = []
            case _:
                raise RuntimeError(f"Unhandled event type: {event['type']}")

    async def send_websocket(self, event: "ASGISendEvent") -> None:
        match event["type"]:
            case "websocket.accept":
                event = cast("WebSocketAcceptEvent", event)
                headers = [
                    (b"Connection", b"Upgrade"),
                    (b"Upgrade", b"websocket"),
                ]
                if subprotocol := event.get("subprotocol", None):
                    headers.append(
                        (b"Sec-Websocket-Protocol", subprotocol.encode())
                    )
                data = self.http_serializer.serialize_metadata(
                    ResponseMetadata(
                        status=101,
                        headers=headers,
                    )
                )
                self.event_bus.send(data)
                self.expected_events = ["websocket.send", "websocket.close"]
            case "websocket.close":
                self.event_bus.send(
                    self.websocket_serializer.build_close_frame()
                )
                self.expected_events = []
            case _:
                raise ValueError(f"Unhandled event type {event['type']}")

    def validate_event_type(self, event_type: str) -> str:
        assert len(self.expected_events) != 0, "No events was expected"
        assert (
            event_type in self.expected_events
        ), f"Unexpected event {event_type}"
        return event_type

    def is_keepalive(self) -> bool:
        return self._is_keepalive
