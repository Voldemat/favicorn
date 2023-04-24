import logging

from asgiref.typing import ASGI3Application

from favicorn.connections.http.icontroller import (
    IHTTPController,
    IHTTPControllerFactory,
)
from favicorn.connections.http.ievent_bus import IHTTPEventBusFactory
from favicorn.connections.http.iparser import IHTTPParserFactory
from favicorn.connections.http.iserializer import (
    IHTTPSerializerFactory,
)


from .controller import HTTPASGIController


class HTTPASGIControllerFactory(IHTTPControllerFactory):
    def __init__(
        self,
        app: ASGI3Application,
        parser_factory: IHTTPParserFactory,
        event_bus_factory: IHTTPEventBusFactory,
        serializer_factory: IHTTPSerializerFactory,
        logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        self.app = app
        self.logger = logger
        self.parser_factory = parser_factory
        self.event_bus_factory = event_bus_factory
        self.serializer_factory = serializer_factory

    def build(self, client: tuple[str, int] | None) -> IHTTPController:
        return HTTPASGIController(
            client=client,
            app=self.app,
            logger=self.logger,
            parser=self.parser_factory.build(),
            event_bus=self.event_bus_factory.build(),
            serializer=self.serializer_factory.build(),
        )
