import asyncio

from asgiref.typing import ASGI3Application

from .asgi_controller import ASGIController
from .parser import HTTPParser
from .serializer import HTTPSerializer
from .utils import get_remote_addr


class Connection:
    def __init__(
        self,
        app: ASGI3Application,
        parser: HTTPParser,
        serializer: HTTPSerializer,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.app = app
        self.parser = parser
        self.serializer = serializer
        self.client = get_remote_addr(writer)
        self.keepalive = True

    async def init(self) -> None:
        pass

    async def main(self) -> None:
        while self.keepalive:
            data = await asyncio.wait_for(self.read(), timeout=5)
            await self.handle_request(data)

    async def handle_request(self, data: bytes) -> None:
        asgi_controller = ASGIController(
            self.app,
            root_path="",
            client=self.client,
            server=("localhost", 8000),
        )
        self.parser.feed_data(data)
        while not self.parser.state.is_metadata_ready():
            self.parser.feed_data(await self.read())

        metadata = self.parser.state.get_metadata()
        async for event in asgi_controller.start(metadata):
            if event["type"] == "receive":
                if not self.parser.has_body():
                    self.parser.feed_data(await self.read())
                body = self.parser.get_body()
                assert body is not None
                asgi_controller.receive_body(body, self.parser.state.more_body)
            if event["type"] == "send-metadata":
                self.serializer.receive_metadata(event["metadata"])
                data = self.serializer.get_data()
                self.write(data)
            if event["type"] == "send-body":
                self.serializer.feed_body(event["body"], event["more_body"])
                data = self.serializer.get_data()
                self.write(data)

        await self.writer.drain()
        self.keepalive = self.parser.state.is_keepalive()

    async def read(self) -> bytes:
        return await self.reader.read(4028)

    def write(self, data: bytes) -> None:
        self.writer.write(data)

    async def close(self) -> None:
        if self.writer.can_write_eof():
            self.writer.write_eof()
        self.writer.close()
        await self.writer.wait_closed()
