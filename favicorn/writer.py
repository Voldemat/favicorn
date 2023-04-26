import asyncio

from .utils import get_remote_addr


class SocketWriter:
    stream_writer: asyncio.StreamWriter

    def __init__(self, stream_writer: asyncio.StreamWriter) -> None:
        self.stream_writer = stream_writer

    def write(self, data: bytes) -> None:
        if not self.stream_writer.is_closing():
            self.stream_writer.write(data)

    async def flush(self) -> None:
        if not self.stream_writer.is_closing():
            await self.stream_writer.drain()

    def is_closing(self) -> bool:
        return self.stream_writer.is_closing()

    def get_address(self) -> tuple[str, int] | None:
        return get_remote_addr(self.stream_writer)

    async def close(self) -> None:
        if self.stream_writer.is_closing():
            return
        if self.stream_writer.can_write_eof():
            self.stream_writer.write_eof()
        self.stream_writer.close()
        await self.stream_writer.wait_closed()
