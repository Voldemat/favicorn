import socket
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Awaitable, Callable

from favicorn import Favicorn, HTTPProtocol, InetSocketProvider


@asynccontextmanager
async def serving_app(
    app: Callable[[Any, Any, Any], Awaitable[None]], host: str, port: int
) -> AsyncGenerator[Favicorn, None]:
    s = Favicorn(
        app=app,
        socket_provider=InetSocketProvider(
            host=host,
            port=port,
            family=socket.AddressFamily.AF_INET,
            reuse_address=True,
        ),
        protocol_class=HTTPProtocol,
    )
    await s.init()
    await s.start_serving()
    yield s
    await s.close()
