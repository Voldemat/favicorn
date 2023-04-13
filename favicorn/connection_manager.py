import asyncio

from .iconnection_factory import IConnectionFactory


class ConnectionManager:
    def __init__(
        self,
        connection_factory: IConnectionFactory,
    ) -> None:
        self.connection_factory = connection_factory

    async def handler(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        connection = self.connection_factory.build(
            reader,
            writer,
        )
        await connection.init()
        try:
            await connection.main()
        finally:
            await connection.close()
