from asgiref.typing import ASGI3Application

from favicorn.connections.http.icontroller import (
    IHTTPController,
    IHTTPControllerFactory,
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
        parser_factory: IHTTPParserFactory,
        serializer_factory: IHTTPSerializerFactory,
    ) -> None:
        self.app = app
        self.parser_factory = parser_factory
        self.serializer_factory = serializer_factory

    def build(self, client: tuple[str, int] | None) -> IHTTPController:
        return HTTPASGIController(
            app=self.app,
            parser=self.parser_factory.build(),
            serializer=self.serializer_factory.build(),
            client=client,
        )
