import logging

from asgiref.typing import ASGI3Application

from favicorn.i.controller import (
    IController,
    IControllerFactory,
)
from favicorn.i.event_bus import IEventBusFactory
from favicorn.i.protocols.http.parser import IHTTPParserFactory
from favicorn.i.protocols.http.serializer import (
    IHTTPSerializerFactory,
)
from favicorn.i.protocols.websocket.parser import IWebsocketParserFactory
from favicorn.i.protocols.websocket.serializer import (
    IWebsocketSerializerFactory,
)

from .controller import ASGIController


class ASGIControllerFactory(IControllerFactory):
    def __init__(
        self,
        app: ASGI3Application,
        event_bus_factory: IEventBusFactory,
        http_protocol: tuple[IHTTPParserFactory, IHTTPSerializerFactory],
        websocket_protocol: tuple[
            IWebsocketParserFactory, IWebsocketSerializerFactory
        ]
        | None = None,
        logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        self.app = app
        self.logger = logger
        self.event_bus_factory = event_bus_factory
        self.http_protocol = http_protocol
        self.websocket_protocol = websocket_protocol

    def build(self) -> IController:
        return ASGIController(
            app=self.app,
            logger=self.logger,
            event_bus=self.event_bus_factory.build(),
            http_parser=self.http_protocol[0].build(),
            http_serializer=self.http_protocol[1].build(),
            websocket_parser=self.websocket_protocol[0].build()
            if self.websocket_protocol is not None
            else None,
            websocket_serializer=self.websocket_protocol[1].build()
            if self.websocket_protocol is not None
            else None,
        )
