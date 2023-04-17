import asyncio

from .connection_manager import ConnectionManager
from .iconnection import IConnectionFactory
from .isocket_provider import ISocketProvider


class Server:
    socket_provider: ISocketProvider
    connection_factory: IConnectionFactory

    def __init__(
        self,
        socket_provider: ISocketProvider,
        connection_factory: IConnectionFactory,
    ) -> None:
        self.socket_provider = socket_provider
        self.connection_factory = connection_factory

    async def init(self) -> None:
        sock = self.socket_provider.acquire()
        manager = ConnectionManager(self.connection_factory)
        self._server = await asyncio.start_server(
            manager.handler,
            sock=sock,
            start_serving=False,
        )

    async def close(self) -> None:
        if self._server is not None and self._server.is_serving():
            self._server.close()
            await self._server.wait_closed()
        self.socket_provider.cleanup()

    async def start_serving(self) -> None:
        await self._server.start_serving()

    async def serve_forever(self) -> None:
        await self._server.serve_forever()
