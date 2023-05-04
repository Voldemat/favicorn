import asyncio

from .i.connection import IConnectionFactory
from .reader import SocketReader
from .writer import SocketWriter


class ConnectionManager:
    def __init__(
        self,
        connection_factory: IConnectionFactory,
    ) -> None:
        self.connection_factory = connection_factory

    async def handler(
        self,
        stream_reader: asyncio.StreamReader,
        stream_writer: asyncio.StreamWriter,
    ) -> None:
        connection = self.connection_factory.build(
            reader=SocketReader(
                stream_reader=stream_reader, default_read_count=4028
            ),
            writer=SocketWriter(stream_writer=stream_writer),
        )
        try:
            await connection.main()
        finally:
            await connection.close()
