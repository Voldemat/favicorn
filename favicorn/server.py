import asyncio
import logging

from .connection_manager import ConnectionManager
from .i.connection import IConnectionFactory
from .i.socket_provider import ISocketProvider


class Server:
    logger: logging.Logger
    socket_provider: ISocketProvider
    connection_factory: IConnectionFactory

    def __init__(
        self,
        socket_provider: ISocketProvider,
        connection_factory: IConnectionFactory,
        logger: logging.Logger = logging.getLogger(__name__),
    ) -> None:
        self.logger = logger
        self.socket_provider = socket_provider
        self.connection_factory = connection_factory

    async def init(self) -> None:
        self.logger.debug("Start initializing server")
        sock = self.socket_provider.acquire()
        self.logger.info(
            f"Socket {sock.getsockname()} acquired successfully "
            f"using {type(self.socket_provider)}"
        )
        manager = ConnectionManager(self.connection_factory)
        self._server = await asyncio.start_server(
            manager.handler,
            sock=sock,
            start_serving=False,
        )
        self.logger.debug("Initialization is complete")

    async def start_serving(self) -> None:
        self.logger.debug("Start serving...")
        await self._server.start_serving()

    async def serve_forever(self) -> None:
        self.logger.info("Serve forever...")
        await self._server.serve_forever()

    async def close(self) -> None:
        self.logger.debug("Closing server...")
        if self._server is not None and self._server.is_serving():
            self._server.close()
            self.logger.debug("Wait for async server to close...")
            await self._server.wait_closed()
        self.socket_provider.cleanup()
        self.logger.info("Server closed successfully")
