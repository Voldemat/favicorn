import asyncio
from typing import Any

from .iglobal_state import IGlobalState


class GlobalState(IGlobalState):
    tasks: set[asyncio.Task[Any]]
    tasks_wait_timeout: float

    def __init__(self, tasks_wait_timeout: float = 5) -> None:
        self.tasks = set()
        self.tasks_wait_timeout = tasks_wait_timeout

    def add_task(self, task: asyncio.Task[Any]) -> None:
        self.tasks.add(task)
        task.add_done_callback(self.remove_task)

    def remove_task(self, task: asyncio.Task[Any]) -> None:
        self.tasks.remove(task)

    async def cancel_all_tasks(self) -> None:
        await self.wait_for_tasks_completion()
        for task in self.tasks:
            task.cancel()
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            pass

    async def wait_for_tasks_completion(self) -> None:
        await asyncio.wait_for(
            asyncio.gather(*self.tasks), timeout=self.tasks_wait_timeout
        )
