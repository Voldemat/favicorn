import logging

from asgiref.typing import ASGI3Application

from favicorn.connections.http.icontroller import (
    IHTTPController,
    IHTTPControllerFactory,
)
from favicorn.connections.http.ievent_bus import (
    IHTTPEventBus,
    IHTTPEventBusFactory,
)
from favicorn.connections.http.iparser import IHTTPParserFactory
from favicorn.connections.http.iserializer import (
    IHTTPSerializerFactory,
)


from .controller import HTTPASGIController


class HTTPASGIControllerFactory(IHTTPControllerFactory):
    def __init__(
        self,
        app: ASGI3Application,
        http_parser_factory: IHTTPParserFactory,
        event_bus_factory: IHTTPEventBusFactory,
        serializer_factory: IHTTPSerializerFactory,
        logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        self.app = app
        self.logger = logger
        self.http_parser_factory = http_parser_factory
        self.event_bus_factory = event_bus_factory
        self.serializer_factory = serializer_factory

    def build(self) -> tuple[IHTTPController, IHTTPEventBus]:
        event_bus = self.event_bus_factory.build()
        return (
            HTTPASGIController(
                app=self.app,
                logger=self.logger,
                http_parser=self.http_parser_factory.build(),
                event_bus=event_bus,
                serializer=self.serializer_factory.build(),
            ),
            event_bus,
        )
