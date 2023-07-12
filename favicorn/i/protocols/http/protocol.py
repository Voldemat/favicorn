from dataclasses import dataclass

from .parser import IHTTPParser, IHTTPParserFactory
from .serializer import IHTTPSerializer, IHTTPSerializerFactory


@dataclass
class HTTPProtocol:
    parser: IHTTPParser
    serializer: IHTTPSerializer


@dataclass
class HTTPProtocolFactory:
    parser_factory: IHTTPParserFactory
    serializer_factory: IHTTPSerializerFactory

    def build(self) -> HTTPProtocol:
        return HTTPProtocol(
            parser=self.parser_factory.build(),
            serializer=self.serializer_factory.build(),
        )
