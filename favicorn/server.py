import asyncio

from asgiref.typing import ASGI3Application

from .connection_manager import ConnectionManager
from .isocket_provider import ISocketProvider
from .parser import HTTPParser
from .serializer import HTTPSerializer


class Server:
    app: ASGI3Application
    socket_provider: ISocketProvider

    def __init__(
        self,
        app: ASGI3Application,
        socket_provider: ISocketProvider,
    ) -> None:
        self.app = app
        self.socket_provider = socket_provider
        self.connection_manager = ConnectionManager(
            app=app,
            parser_class=HTTPParser,
            serializer_class=HTTPSerializer,
        )

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
