from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asgiref.typing import (
        ASGI3Application,
    )

from favicorn.i.controller import IController
from favicorn.i.event_bus import IEventBus
from favicorn.i.protocols.http.parser import IHTTPParser
from favicorn.i.protocols.http.request_metadata import RequestMetadata
from favicorn.i.protocols.http.serializer import IHTTPSerializer
from favicorn.i.protocols.websocket.parser import IWebsocketParser
from favicorn.i.protocols.websocket.serializer import IWebsocketSerializer

from .event_manager import ASGIEventManager


class ASGIController(IController):
    logger: logging.Logger
    event_bus: IEventBus
    http_parser: IHTTPParser
    task: asyncio.Task[None] | None
    event_manager: ASGIEventManager

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
        self.task = None
        self.logger = logger
        self.event_bus = event_bus
        self.http_parser = http_parser
        self.event_manager = ASGIEventManager(
            app=app,
            logger=logger,
            event_bus=event_bus,
            http_parser=http_parser,
            http_serializer=http_serializer,
            websocket_parser=websocket_parser,
            websocket_serializer=websocket_serializer,
        )

    async def start(self, client: tuple[str, int] | None) -> None:
        self.task = asyncio.create_task(self.main(client))

    async def main(self, client: tuple[str, int] | None) -> None:
        await self.event_manager.launch_app(
            metadata=await self.wait_for_metadata(),
            client=client,
        )
        self.event_bus.close()

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

    def get_event_bus(self) -> IEventBus:
        return self.event_bus

    def is_keepalive(self) -> bool:
        return self.event_manager.is_keepalive()
