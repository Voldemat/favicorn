import asyncio
from typing import Type

from asgiref.typing import ASGI3Application

from .global_state import GlobalState
from .http_protocol import HTTPProtocol
from .iglobal_state import IGlobalState
from .iprotocol import IProtocol
from .isocket_provider import ISocketProvider


class Server:
    socket_provider: ISocketProvider
    protocol_class: Type[IProtocol]
    _server: asyncio.Server | None
    app: ASGI3Application
    global_state: IGlobalState

    def __init__(
        self,
        app: ASGI3Application,
        socket_provider: ISocketProvider,
        protocol_class: Type[IProtocol] = HTTPProtocol,
        global_state: IGlobalState | None = None,
    ) -> None:
        if global_state is None:
            global_state = GlobalState()
        self.socket_provider = socket_provider
        self.protocol_class = protocol_class
        self.global_state = global_state
        self._server = None
        self.app = app

    @property
    def server(self) -> asyncio.Server:
        if self._server is None:
            raise ValueError("Server is not initialized yet")
        return self._server

    async def init(self) -> None:
        loop = asyncio.get_running_loop()
        sock = self.socket_provider.acquire()
        self._server = await loop.create_server(
            lambda: self.protocol_class(self.global_state, self.app),
            sock=sock,
            start_serving=False,
        )

    async def close(self) -> None:
        if self._server is not None and self.server.is_serving():
            self.server.close()
            await self.server.wait_closed()
        self.socket_provider.cleanup()

    async def start_serving(self) -> None:
        await self.server.start_serving()

    async def serve_forever(self) -> None:
        await self.server.serve_forever()
