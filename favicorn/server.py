import asyncio
from typing import Type

from asgiref.typing import ASGI3Application

from .config import Config
from .global_state import GlobalState
from .http_protocol import HTTPProtocol
from .iglobal_state import IGlobalState
from .iprotocol import IProtocol
from .isocket_provider import ISocketProvider
from .keepalive_manager import KeepAliveManager


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
        config: Config | None = None,
    ) -> None:
        if config is None:
            config = Config()
        self.socket_provider = socket_provider
        self.protocol_class = protocol_class
        self.global_state = GlobalState(config=config)
        self._server = None
        self.app = app
        self.keepalive_manager = KeepAliveManager(self.global_state)

    @property
    def server(self) -> asyncio.Server:
        if self._server is None:
            raise ValueError("Server is not initialized yet")
        return self._server

    async def init(self) -> None:
        loop = asyncio.get_running_loop()
        sock = self.socket_provider.acquire()

        def factory() -> IProtocol:
            connection = self.protocol_class(self.app)
            self.global_state.add_connection(connection)
            return connection

        self._server = await loop.create_server(
            factory,
            sock=sock,
            start_serving=False,
        )
        await self.keepalive_manager.start()

    async def close(self) -> None:
        await self.keepalive_manager.stop()
        if self._server is not None and self.server.is_serving():
            self.server.close()
            await self.server.wait_closed()
        await self.global_state.discard_all_connections()
        self.socket_provider.cleanup()

    async def start_serving(self) -> None:
        await self.server.start_serving()

    async def serve_forever(self) -> None:
        await self.server.serve_forever()
