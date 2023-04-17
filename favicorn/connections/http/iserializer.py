from abc import ABC, abstractmethod

from .response_metadata import ResponseMetadata


class IHTTPSerializer(ABC):
    @abstractmethod
    def serialize_metadata(
        self,
        metadata: ResponseMetadata,
    ) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def serialize_body(self, body: bytes) -> bytes:
        raise NotImplementedError


class IHTTPSerializerFactory(ABC):
    @abstractmethod
    def build(self) -> IHTTPSerializer:
        raise NotImplementedError
