from abc import ABC, abstractmethod


class IConnection(ABC):
    @abstractmethod
    async def init(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def main(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError
