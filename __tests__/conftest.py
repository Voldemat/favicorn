import asyncio
import threading
from contextlib import contextmanager
from typing import Any, Awaitable, Callable, Generator, Sequence, Type

from favicorn import (
    BaseHTTPSerializerFactory,
    Favicorn,
    HTTPASGIControllerFactory,
    HTTPConnectionFactory,
    HTTPToolsParserFactory,
    InetSocketProvider,
)

import httptools


@contextmanager
def serving_app(
    app: Callable[[Any, Any, Any], Awaitable[None]],
    host: str,
    port: int,
    suppress_exceptions: Sequence[Type[BaseException]] = [],
) -> Generator[None, None, None]:
    stop_event = threading.Event()
    app_exception: Exception | None = None

    async def wrapper(*args: Any, **kwargs: Any) -> None:
        try:
            return await app(*args, **kwargs)
        except Exception as error:
            nonlocal app_exception
            app_exception = error

    async def serve(
        event: threading.Event,
        app: Callable[[Any, Any, Any], Awaitable[None]],
        host: str,
        port: int,
    ) -> None:
        s = Favicorn(
            connection_factory=HTTPConnectionFactory(
                controller_factory=HTTPASGIControllerFactory(
                    app,
                    parser_factory=HTTPToolsParserFactory(httptools),
                    serializer_factory=BaseHTTPSerializerFactory(),
                ),
            ),
            socket_provider=InetSocketProvider(
                host=host,
                port=port,
                reuse_address=True,
            ),
        )
        await s.init()
        await s.start_serving()
        while True:
            await asyncio.sleep(0)
            if event.is_set():
                break
        await s.close()

    thread = threading.Thread(
        target=asyncio.run,
        args=(serve(stop_event, wrapper, host, port),),
    )
    thread.start()
    try:
        yield
    finally:
        stop_event.set()
        thread.join()
        if (
            app_exception is not None
            and type(app_exception) not in suppress_exceptions
        ):
            raise app_exception
