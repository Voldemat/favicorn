from abc import ABC, abstractmethod

from .request_metadata import RequestMetadata


class IHTTPParser(ABC):
    @abstractmethod
    def has_body(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_body(self) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def is_metadata_ready(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_metadata(self) -> RequestMetadata:
        raise NotImplementedError

    @abstractmethod
    def is_keepalive(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_more_body(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def feed_data(self, data: bytes) -> None:
        raise NotImplementedError