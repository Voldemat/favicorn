import asyncio

from asgiref.typing import ASGI3Application

from .asgi_controller import ASGIController
from .parser import HTTPParser
from .serializer import HTTPSerializer
from .utils import get_remote_addr


class InternalServer:
    def __init__(
        self,
        app: ASGI3Application,
        parser: HTTPParser,
        serializer: HTTPSerializer,
    ) -> None:
        self.app = app
        self.parser = parser
        self.serializer = serializer

    async def handler(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        asgi_controller = ASGIController(
            self.app,
            root_path="",
            server=("localhost", 8000),
            client=get_remote_addr(writer),
        )
        while not self.parser.state.is_metadata_ready():
            self.parser.feed_data(await reader.read(4028))

        metadata = self.parser.state.get_metadata()
        async for event in asgi_controller.start(metadata):
            if event["type"] == "receive":
                if not self.parser.has_body():
                    self.parser.feed_data(await reader.read(4028))
                body = self.parser.get_body()
                assert body is not None
                asgi_controller.receive_body(body, self.parser.state.more_body)
            if event["type"] == "send-metadata":
                self.serializer.receive_metadata(event["metadata"])
                data = self.serializer.get_data()
                writer.write(data)
            if event["type"] == "send-body":
                self.serializer.feed_body(event["body"], event["more_body"])
                data = self.serializer.get_data()
                writer.write(data)
        await writer.drain()
        if writer.can_write_eof():
            writer.write_eof()
        writer.close()
        await writer.wait_closed()
