import asyncio


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
        if socket_info := self.stream_writer.get_extra_info("socket"):
            if info := socket_info.getpeername():
                return (str(info[0]), int(info[1]))
        if info := self.stream_writer.get_extra_info("peername"):
            return (str(info[0]), int(info[1]))
        return None

    async def close(self) -> None:
        if self.stream_writer.is_closing():
            return
        if self.stream_writer.can_write_eof():
            self.stream_writer.write_eof()
        self.stream_writer.close()
        await self.stream_writer.wait_closed()
