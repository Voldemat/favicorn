import asyncio
import socket
from typing import Callable, Type

from asgiref.typing import ASGI3Application

from .http_protocol import HTTPProtocol
from .iprotocol import IProtocol
from .isocket_provider import ISocketProvider


class Server:
    socket_provider: ISocketProvider
    protocol: Type[asyncio.Protocol]
    sock: socket.socket | None
    server: asyncio.Server | None
    app: ASGI3Application

    def __init__(
        self,
        app: ASGI3Application,
        socket_provider: ISocketProvider,
        protocol_factory: Callable[
            [ASGI3Application], IProtocol
        ] = HTTPProtocol,
    ) -> None:
        self.socket_provider = socket_provider
        self.protocol_factory = protocol_factory
        self.sock = None
        self.server = None
        self.app = app

    async def init(self) -> None:
        loop = asyncio.get_event_loop()
        self.sock = self.socket_provider.acquire()
        self.server = await loop.create_server(
            lambda: self.protocol_factory(self.app),
            sock=self.sock,
            start_serving=False,
        )

    async def shutdown(self) -> None:
        if self.sock is not None:
            self.socket_provider.cleanup()

    async def serve(self) -> None:
        if self.server is None:
            raise ValueError("Server is not initialized yet")
        await self.server.serve_forever()
