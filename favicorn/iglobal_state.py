import asyncio
from abc import ABC, abstractmethod
from typing import Any


class IGlobalState(ABC):
    @abstractmethod
    def add_task(self, task: asyncio.Task[Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def cancel_all_tasks(self) -> None:
        raise NotImplementedError
