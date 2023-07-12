import logging

from asgiref.typing import ASGI3Application

from favicorn.i.controller import (
    IController,
    IControllerFactory,
)
from favicorn.i.event_bus import IEventBusFactory
from favicorn.i.protocols.http.protocol import HTTPProtocolFactory
from favicorn.i.protocols.websocket.protocol import WebsocketProtocolFactory

from .controller import ASGIController


class ASGIControllerFactory(IControllerFactory):
    def __init__(
        self,
        app: ASGI3Application,
        event_bus_factory: IEventBusFactory,
        http_protocol_factory: HTTPProtocolFactory,
        websocket_protocol_factory: WebsocketProtocolFactory | None = None,
        logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        self.app = app
        self.logger = logger
        self.event_bus_factory = event_bus_factory
        self.http_protocol_factory = http_protocol_factory
        self.websocket_protocol_factory = websocket_protocol_factory

    def build(self) -> IController:
        return ASGIController(
            app=self.app,
            logger=self.logger,
            event_bus=self.event_bus_factory.build(),
            http_protocol=self.http_protocol_factory.build(),
            websocket_protocol=self.websocket_protocol_factory.build()
            if self.websocket_protocol_factory is not None
            else None,
        )
