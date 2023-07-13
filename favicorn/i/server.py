from abc import ABC, abstractmethod


class IServer(ABC):
    @abstractmethod
    async def init(self) -> None:
        pass

    @abstractmethod
    async def start_serving(self) -> None:
        pass

    @abstractmethod
    async def serve_forever(self) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
