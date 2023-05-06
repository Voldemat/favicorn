from abc import ABC, abstractmethod


class IWebsocketParser(ABC):
    @abstractmethod
    def feed_data(self, data: bytes) -> None:
        pass

    @abstractmethod
    def get_data(self) -> str | bytes | int | None:
        pass


class IWebsocketParserFactory(ABC):
    @abstractmethod
    def build(self) -> IWebsocketParser:
        pass
