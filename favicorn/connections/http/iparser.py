from abc import ABC, abstractmethod

from .request_metadata import RequestMetadata


class HTTPParsingException(BaseException):
    pass


class IHTTPParser(ABC):
    @abstractmethod
    def feed_data(self, data: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_metadata_ready(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_metadata(self) -> RequestMetadata:
        raise NotImplementedError

    @abstractmethod
    def has_error(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_error(self) -> HTTPParsingException:
        raise NotImplementedError

    @abstractmethod
    def has_body(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_body(self) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def is_more_body(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_keepalive(self) -> bool:
        raise NotImplementedError


class IHTTPParserFactory(ABC):
    @abstractmethod
    def build(self) -> IHTTPParser:
        raise NotImplementedError
