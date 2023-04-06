import asyncio
from typing import Type

from asgiref.typing import ASGI3Application

from .connection import Connection
from .parser import HTTPParser
from .serializer import HTTPSerializer


class ConnectionFactory:
    def __init__(
        self,
        app: ASGI3Application,
        parser_class: Type[HTTPParser],
        serializer_class: Type[HTTPSerializer],
    ) -> None:
        self.app = app
        self.parser_class = parser_class
        self.serializer_class = serializer_class

    def build(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> Connection:
        return Connection(
            self.app,
            self.parser_class(),
            self.serializer_class(),
            reader,
            writer,
        )
