import asyncio
from typing import Any, Iterable

from .config import Config
from .iglobal_state import IGlobalState
from .iprotocol import IProtocol


class GlobalState(IGlobalState):
    connections: list[IProtocol]
    config: Config

    def __init__(
        self,
        config: Config,
    ) -> None:
        self.connections = []
        self.config = config

    def get_config(self) -> Config:
        return self.config

    def add_connection(self, connection: IProtocol) -> None:
        self.connections.append(connection)

    def get_connections(self) -> list[IProtocol]:
        return self.connections

    async def discard_all_connections(self) -> None:
        await self.wait_for_tasks_completion()
        for task in self.get_app_tasks():
            task.cancel()
        try:
            await asyncio.gather(*self.get_app_tasks())
        except asyncio.CancelledError:
            pass

    def get_app_tasks(self) -> Iterable[asyncio.Task[Any]]:
        return map(lambda conn: conn.get_app_task(), self.connections)

    async def wait_for_tasks_completion(self) -> None:
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.get_app_tasks()),
                timeout=self.config.tasks_wait_timeout_s,
            )
        except asyncio.TimeoutError:
            pass
