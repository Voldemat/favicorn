import asyncio
from typing import Type

from asgiref.typing import ASGI3Application

from .iprotocol import IProtocol
from .isocket_provider import ISocketProvider


class Server:
    socket_provider: ISocketProvider
    protocol_class: Type[IProtocol]
    server: asyncio.Server | None
    app: ASGI3Application

    def __init__(
        self,
        app: ASGI3Application,
        socket_provider: ISocketProvider,
        protocol_class: Type[IProtocol],
    ) -> None:
        self.socket_provider = socket_provider
        self.protocol_class = protocol_class
        self.server = None
        self.app = app

    async def init(self) -> None:
        loop = asyncio.get_running_loop()
        sock = self.socket_provider.acquire()
        self.server = await loop.create_server(
            lambda: self.protocol_class(self.app),
            sock=sock,
            start_serving=False,
        )

    async def close(self) -> None:
        if self.server is not None and self.server.is_serving():
            self.server.close()
            await self.server.wait_closed()
        self.socket_provider.cleanup()

    async def start_serving(self) -> None:
        if self.server is None:
            raise ValueError("Server is not initialized yet")
        await self.server.start_serving()
