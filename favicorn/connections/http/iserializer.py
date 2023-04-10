from abc import ABC, abstractmethod

from .response_metadata import ResponseMetadata


class IHTTPSerializer(ABC):
    @abstractmethod
    def receive_metadata(
        self,
        metadata: ResponseMetadata,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def receive_body(self, body: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_data(self) -> bytes:
        raise NotImplementedError
