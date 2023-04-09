import asyncio

from .iconnection_manager import IConnectionManager
from .isocket_provider import ISocketProvider


class Server:
    socket_provider: ISocketProvider
    connection_manager: IConnectionManager

    def __init__(
        self,
        socket_provider: ISocketProvider,
        connection_manager: IConnectionManager,
    ) -> None:
        self.socket_provider = socket_provider
        self.connection_manager = connection_manager

    async def init(self) -> None:
        sock = self.socket_provider.acquire()
        self._server = await asyncio.start_server(
            self.connection_manager.handler,
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
