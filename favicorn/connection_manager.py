import asyncio
from typing import Type

from asgiref.typing import ASGI3Application

from .connection_factory import ConnectionFactory
from .parser import HTTPParser
from .serializer import HTTPSerializer


class ConnectionManager:
    def __init__(
        self,
        app: ASGI3Application,
        parser_class: Type[HTTPParser],
        serializer_class: Type[HTTPSerializer],
    ) -> None:
        self.connection_factory = ConnectionFactory(
            app,
            parser_class,
            serializer_class,
        )

    async def handler(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        connection = self.connection_factory.build(reader, writer)
        await connection.init()
        await connection.main()
        await connection.close()
