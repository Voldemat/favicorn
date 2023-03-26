import asyncio
from typing import Any

from .iglobal_state import IGlobalState


class GlobalState(IGlobalState):
    tasks: set[asyncio.Task[Any]]

    def __init__(self) -> None:
        self.tasks = set()

    def add_task(self, task: asyncio.Task[Any]) -> None:
        self.tasks.add(task)
        task.add_done_callback(self.remove_task)

    def remove_task(self, task: asyncio.Task[Any]) -> None:
        self.tasks.remove(task)
