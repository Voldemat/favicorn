import asyncio
from datetime import datetime, timedelta
from typing import Any

from .iglobal_state import IGlobalState
from .iprotocol import IProtocol


class KeepAliveManager:
    task: asyncio.Task[Any] | None
    global_state: IGlobalState

    def __init__(self, global_state: IGlobalState) -> None:
        self.global_state = global_state
        self.task = None

    async def start(self) -> None:
        self.task = asyncio.create_task(self.main())
        self.task.add_done_callback(self.task_done_callback)

    async def main(self) -> None:
        while True:
            for conn in filter(
                self.is_conn_needed_to_close,
                self.global_state.get_connections(),
            ):
                conn.close()
            await asyncio.sleep(0.001)

    def task_done_callback(self, task: asyncio.Task[Any]) -> None:
        exc = task.exception()
        if exc is not None and not isinstance(exc, asyncio.CancelledError):
            raise exc
        self.task = None

    def is_conn_needed_to_close(self, conn: IProtocol) -> bool:
        if conn.is_keepalive() is False:
            return False
        timestamp = conn.get_latest_received_data_timestamp()
        if timestamp is None:
            return False
        return timestamp < (
            datetime.now()
            - timedelta(
                seconds=self.global_state.get_config().keepalive_timeout_s
            )
        )

    async def stop(self) -> None:
        if self.task is None or self.task.cancelled():
            return
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass
