import asyncio


class SocketReader:
    buffered_data: bytes | None
    stream_reader: asyncio.StreamReader
    default_read_count: int

    def __init__(
        self, stream_reader: asyncio.StreamReader, default_read_count: int
    ) -> None:
        self.buffered_data = None
        self.stream_reader = stream_reader
        self.default_read_count = default_read_count

    async def read(
        self, timeout: float | None = None, count: int | None = None
    ) -> bytes | None:
        if self.buffered_data is not None:
            data = self.buffered_data
            self.buffered_data = None
            return data
        if timeout is None:
            return await self._read(count=count)
        try:
            return await asyncio.wait_for(
                self._read(count=count), timeout=timeout
            )
        except asyncio.TimeoutError:
            return None

    async def _read(self, count: int | None = None) -> bytes | None:
        if count is None:
            count = self.default_read_count
        data = await self.stream_reader.read(count)
        if self.stream_reader.at_eof():
            return None
        return data

    async def wait(self, timeout: int | None = None) -> bool:
        if data := await self.read(timeout=timeout, count=None):
            self.buffered_data = data
            return True
        return False
