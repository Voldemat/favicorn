from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asgiref.typing import (
        ASGI3Application,
        WWWScope,
    )

from favicorn.i.controller import IController
from favicorn.i.event_bus import IEventBus
from favicorn.i.http.parser import IHTTPParser
from favicorn.i.http.request_metadata import RequestMetadata
from favicorn.i.http.response_metadata import ResponseMetadata
from favicorn.i.http.serializer import IHTTPSerializer

from .event_manager import ASGIEventManager
from .responses import (
    PredefinedResponse,
    RESPONSE_400,
    RESPONSE_500,
)
from .scope_builder import ASGIScopeBuilder


class HTTPASGIController(IController):
    app: "ASGI3Application"
    task: asyncio.Task[None] | None
    response_metadata: ResponseMetadata | None
    http_parser: IHTTPParser
    event_bus: IEventBus
    serializer: IHTTPSerializer
    logger: logging.Logger
    request_path: str | None
    scope: "WWWScope" | None

    def __init__(
        self,
        app: "ASGI3Application",
        http_parser: IHTTPParser,
        serializer: IHTTPSerializer,
        event_bus: IEventBus,
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
        self._is_keepalive = False
        self.scope_builder = ASGIScopeBuilder()
        self.event_manager = ASGIEventManager(
            http_parser=http_parser,
            event_bus=event_bus,
            http_serializer=serializer,
            app=app,
        )

    async def start(self, client: tuple[str, int] | None) -> None:
        self.task = asyncio.create_task(self.main(client))

    async def main(self, client: tuple[str, int] | None) -> None:
        try:
            result = await self.build_asgi_scope(client)
            if result[0] is None:
                self.send_predefined_response(result[1])
            else:
                self.scope = result[0]
                await self.event_manager.launch_app(self.scope)
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
        self._is_keepalive = metadata.is_keepalive()
        scope = self.scope_builder.build(metadata, client)
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

    def log_response(self, status: int) -> None:
        self.logger.info(f"[{status}] - {self.request_path}")

    def send_predefined_response(self, response: PredefinedResponse) -> None:
        data = self.serializer.serialize_metadata(
            response.metadata
        ) + self.serializer.serialize_body(response.body)
        self.log_response(response.metadata.status)
        self.event_bus.send(data)

    def get_event_bus(self) -> IEventBus:
        return self.event_bus

    def is_keepalive(self) -> bool:
        return self._is_keepalive
