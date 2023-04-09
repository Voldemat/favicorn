from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator

from .parser import RequestMetadata
from .serializer import ResponseMetadata


@dataclass
class HTTPControllerReceiveEvent:
    pass


@dataclass
class HTTPControllerSendMetadataEvent:
    metadata: ResponseMetadata


@dataclass
class HTTPControllerSendBodyEvent:
    body: bytes


HTTPControllerEvent = (
    HTTPControllerReceiveEvent
    | HTTPControllerSendMetadataEvent
    | HTTPControllerSendBodyEvent
)


class IHTTPController(ABC):
    @abstractmethod
    def start(
        self, metadata: RequestMetadata
    ) -> AsyncGenerator[HTTPControllerEvent, None]:
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
