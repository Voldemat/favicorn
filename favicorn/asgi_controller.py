from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveEvent,
    ASGISendEvent,
    HTTPDisconnectEvent,
    HTTPRequestEvent,
)

from .request_parser import HTTPRequestParser
from .response_parser import HTTPResponseParser


class ASGIController:
    app: ASGI3Application
    body: bytes | None
    request_parser: HTTPRequestParser
    response_parser: HTTPResponseParser

    def __init__(
        self,
        app: ASGI3Application,
        request_parser: HTTPRequestParser,
        response_parser: HTTPResponseParser,
    ) -> None:
        self.app = app
        self.request_parser = request_parser
        self.response_parser = response_parser

    async def start(self) -> None:
        scope = await self.request_parser.get_scope()
        await self.app(scope, self.receive, self.send)

    async def receive(self) -> ASGIReceiveEvent:
        body, more_body = await self.request_parser.receive_body()
        if body is None:
            return HTTPDisconnectEvent(type="http.disconnect")
        return HTTPRequestEvent(
            type="http.request",
            body=body,
            more_body=more_body,
        )

    async def send(self, event: ASGISendEvent) -> None:
        self.response_parser.send(event)
