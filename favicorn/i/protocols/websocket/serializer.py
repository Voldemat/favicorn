from abc import ABC, abstractmethod


class IWebsocketSerializer(ABC):
    @abstractmethod
    def create_accept_token(self, client_token: bytes) -> bytes:
        pass

    @abstractmethod
    def serialize_data(self, data: bytes | str) -> bytes:
        pass

    @abstractmethod
    def build_close_frame(self) -> bytes:
        pass


class IWebsocketSerializerFactory(ABC):
    @abstractmethod
    def build(self, is_client: bool = False) -> IWebsocketSerializer:
        pass
