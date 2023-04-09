from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from .parser import RequestMetadata


class IHTTPController(ABC):
    @abstractmethod
    def start(
        self, metadata: RequestMetadata
    ) -> AsyncGenerator[dict[str, Any], None]:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def receive_body(self, body: bytes, more_body: bool) -> None:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError
