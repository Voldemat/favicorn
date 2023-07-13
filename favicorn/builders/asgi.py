from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from asgiref.typing import ASGI3Application

try:
    import httptools
except ImportError:
    httptools = None

try:
    import h11
except ImportError:
    h11 = None  # type: ignore [assignment]

try:
    import wsproto
except ImportError:
    wsproto = None  # type: ignore [assignment]

from ..connections import TCPConnectionFactory
from ..controllers.asgi import ASGIControllerFactory
from ..event_buses import DequeEventBusFactory
from ..i.builder import IBuilder
from ..i.protocols.http.parser import IHTTPParserFactory
from ..i.protocols.http.protocol import HTTPProtocolFactory
from ..i.protocols.websocket.protocol import WebsocketProtocolFactory
from ..i.server import IServer
from ..protocols.http.parsers import (
    H11HTTPParserFactory,
    HTTPToolsParserFactory,
)
from ..protocols.http.serializers import HTTPBaseSerializerFactory
from ..protocols.websocket.parsers import WSProtoWebsocketParserFactory
from ..protocols.websocket.serializers import (
    WSProtoWebsocketSerializerFactory,
)
from ..server import Server
from ..socket_providers import InetSocketProvider


HTTPParserImpl = Literal["httptools"] | Literal["h11"]
WSImpl = Literal["wsproto"]


class ASGIServerBuilder(IBuilder):
    ws_protocol: WebsocketProtocolFactory | None
    h_parser_factory: IHTTPParserFactory

    def __init__(
        self,
        app: "ASGI3Application",
        http_parser_impl: HTTPParserImpl,
        host: str = "127.0.0.1",
        port: int = 8000,
        ws_impl: WSImpl | None = None,
    ) -> None:
        self.app = app
        self.inet_provider = InetSocketProvider(
            host=host,
            port=port,
            reuse_address=True,
        )
        self.init_http_parser(http_parser_impl)
        self.init_ws_protocol(ws_impl)

    def init_http_parser(self, impl: HTTPParserImpl) -> None:
        match impl:
            case "httptools":
                assert httptools is not None, "httptools is not installed"
                self.h_parser_factory = HTTPToolsParserFactory(httptools)
            case "h11":
                assert h11 is not None, "h11 is not installed"
                self.h_parser_factory = H11HTTPParserFactory(h11)
            case _:
                raise ValueError(
                    f"{impl} http parser implementation is unknown"
                )

    def init_ws_protocol(self, impl: WSImpl | None) -> None:
        if impl is None:
            self.ws_protocol = None
            return
        match impl:
            case "wsproto":
                assert wsproto is not None, "wsproto is not installed"
                self.ws_protocol = WebsocketProtocolFactory(
                    WSProtoWebsocketParserFactory(wsproto),
                    WSProtoWebsocketSerializerFactory(wsproto),
                )
            case _:
                raise ValueError(
                    f"{impl} websocket protocol implementation is unknown"
                )

    def build(self) -> IServer:
        return Server(
            connection_factory=TCPConnectionFactory(
                controller_factory=ASGIControllerFactory(
                    app=self.app,
                    event_bus_factory=DequeEventBusFactory(),
                    http_protocol_factory=HTTPProtocolFactory(
                        self.h_parser_factory,
                        HTTPBaseSerializerFactory(),
                    ),
                    websocket_protocol_factory=self.ws_protocol,
                ),
            ),
            socket_provider=self.inet_provider,
        )
