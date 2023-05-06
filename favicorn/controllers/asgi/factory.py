import logging

from asgiref.typing import ASGI3Application

from favicorn.i.controller import (
    IController,
    IControllerFactory,
)
from favicorn.i.event_bus import IEventBusFactory
from favicorn.i.http.parser import IHTTPParserFactory
from favicorn.i.http.serializer import (
    IHTTPSerializerFactory,
)
from favicorn.i.websocket.parser import IWebsocketParserFactory
from favicorn.i.websocket.serializer import IWebsocketSerializerFactory

from .controller import ASGIController


class ASGIControllerFactory(IControllerFactory):
    def __init__(
        self,
        app: ASGI3Application,
        event_bus_factory: IEventBusFactory,
        http_parser_factory: IHTTPParserFactory,
        http_serializer_factory: IHTTPSerializerFactory,
        websocket_parser_factory: IWebsocketParserFactory | None = None,
        websocket_serializer_factory: IWebsocketSerializerFactory
        | None = None,
        logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        self.app = app
        self.logger = logger
        self.event_bus_factory = event_bus_factory
        self.http_parser_factory = http_parser_factory
        self.http_serializer_factory = http_serializer_factory
        self.websocket_parser_factory = websocket_parser_factory
        self.websocket_serializer_factory = websocket_serializer_factory

    def build(self) -> IController:
        return ASGIController(
            app=self.app,
            logger=self.logger,
            event_bus=self.event_bus_factory.build(),
            http_parser=self.http_parser_factory.build(),
            http_serializer=self.http_serializer_factory.build(),
            websocket_parser=self.websocket_parser_factory.build()
            if self.websocket_parser_factory is not None
            else None,
            websocket_serializer=self.websocket_serializer_factory.build()
            if self.websocket_serializer_factory is not None
            else None,
        )
