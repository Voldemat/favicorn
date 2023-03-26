from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveEvent,
    ASGISendEvent,
    ASGIVersions,
    HTTPDisconnectEvent,
    HTTPRequestEvent,
    HTTPResponseBodyEvent,
    HTTPResponseStartEvent,
    HTTPScope,
)

from .request_parser import HTTPRequestParser
from .response_serializer import HTTPResponseSerializer


class ASGIController:
    app: ASGI3Application
    body: bytes | None
    request_parser: HTTPRequestParser
    response_serializer: HTTPResponseSerializer

    def __init__(
        self,
        app: ASGI3Application,
        request_parser: HTTPRequestParser,
        response_serializer: HTTPResponseSerializer,
    ) -> None:
        self.app = app
        self.request_parser = request_parser
        self.response_serializer = response_serializer

    async def start(self) -> None:
        request = await self.request_parser.get_request()
        scope = HTTPScope(
            type="http",
            asgi=ASGIVersions(spec_version="3.0", version="3.0"),
            http_version=request.http_version,
            scheme=request.scheme,
            path=request.path,
            raw_path=request.raw_path,
            query_string=request.query_string,
            root_path=request.root_path,
            headers=request.headers,
            server=request.server,
            client=request.client,
            extensions={},
            method=request.method,
        )
        try:
            await self.app(scope, self.receive, self.send)
        except BaseException as unhandled_error:
            print(unhandled_error)
            await self.send_500_response()

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
        self.response_serializer.send(event)

    async def send_500_response(self) -> None:
        await self.send(
            HTTPResponseStartEvent(
                type="http.response.start",
                status=500,
                headers=[],
                trailers=False,
            )
        )
        await self.send(
            HTTPResponseBodyEvent(
                type="http.response.body",
                body=b"Internal Server Error",
                more_body=False,
            )
        )
