from dataclasses import dataclass

from .parser import IWebsocketParser, IWebsocketParserFactory
from .serializer import IWebsocketSerializer, IWebsocketSerializerFactory


@dataclass
class WebsocketProtocol:
    parser: IWebsocketParser
    serializer: IWebsocketSerializer


@dataclass
class WebsocketProtocolFactory:
    parser_factory: IWebsocketParserFactory
    serializer_factory: IWebsocketSerializerFactory

    def build(self) -> WebsocketProtocol:
        return WebsocketProtocol(
            parser=self.parser_factory.build(),
            serializer=self.serializer_factory.build(),
        )
