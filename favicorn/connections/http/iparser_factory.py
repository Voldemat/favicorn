from abc import ABC, abstractmethod

from .iparser import IHTTPParser


class IHTTPParserFactory(ABC):
    @abstractmethod
    def build(self) -> IHTTPParser:
        raise NotImplementedError
