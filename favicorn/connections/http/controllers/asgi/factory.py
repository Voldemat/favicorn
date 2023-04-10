from asgiref.typing import ASGI3Application

from favicorn.connections.http.icontroller import IHTTPController
from favicorn.connections.http.icontroller_factory import (
    IHTTPControllerFactory,
)

from .controller import HTTPASGIController


class HTTPASGIControllerFactory(IHTTPControllerFactory):
    def __init__(self, app: ASGI3Application) -> None:
        self.app = app

    def build(self, client: tuple[str, int] | None) -> IHTTPController:
        return HTTPASGIController(app=self.app, client=client)
