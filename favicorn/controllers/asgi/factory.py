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

from .controller import HTTPASGIController


class HTTPASGIControllerFactory(IControllerFactory):
    def __init__(
        self,
        app: ASGI3Application,
        http_parser_factory: IHTTPParserFactory,
        event_bus_factory: IEventBusFactory,
        serializer_factory: IHTTPSerializerFactory,
        logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        self.app = app
        self.logger = logger
        self.http_parser_factory = http_parser_factory
        self.event_bus_factory = event_bus_factory
        self.serializer_factory = serializer_factory

    def build(self) -> IController:
        return HTTPASGIController(
            app=self.app,
            logger=self.logger,
            http_parser=self.http_parser_factory.build(),
            event_bus=self.event_bus_factory.build(),
            serializer=self.serializer_factory.build(),
        )
