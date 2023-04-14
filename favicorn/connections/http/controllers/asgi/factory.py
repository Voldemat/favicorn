from typing import Callable

from asgiref.typing import ASGI3Application

from favicorn.connections.http.icontroller import IHTTPController
from favicorn.connections.http.icontroller_factory import (
    IHTTPControllerFactory,
)
from favicorn.connections.http.iparser_factory import IHTTPParserFactory
from favicorn.connections.http.iserializer import IHTTPSerializer


from .controller import HTTPASGIController


class HTTPASGIControllerFactory(IHTTPControllerFactory):
    def __init__(
        self,
        app: ASGI3Application,
        parser_factory: IHTTPParserFactory,
        serializer_factory: Callable[[], IHTTPSerializer],
    ) -> None:
        self.app = app
        self.parser_factory = parser_factory
        self.serializer_factory = serializer_factory

    def build(self, client: tuple[str, int] | None) -> IHTTPController:
        return HTTPASGIController(
            app=self.app,
            parser=self.parser_factory.build(),
            serializer=self.serializer_factory(),
            client=client,
        )
