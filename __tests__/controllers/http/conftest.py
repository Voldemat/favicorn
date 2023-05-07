from favicorn.i.protocols.http.parser import IHTTPParserFactory
from favicorn.i.protocols.http.serializer import IHTTPSerializerFactory
from favicorn.i.protocols.websocket.parser import IWebsocketParserFactory
from favicorn.i.protocols.websocket.serializer import (
    IWebsocketSerializerFactory,
)
from favicorn.protocols.http.parsers import (
    H11HTTPParserFactory,
    HTTPToolsParserFactory,
)
from favicorn.protocols.http.serializers import HTTPBaseSerializerFactory
from favicorn.protocols.websocket.parsers import (
    WSProtoWebsocketParserFactory,
)
from favicorn.protocols.websocket.serializers import (
    WSProtoWebsocketSerializerFactory,
)

import h11

import httptools

import wsproto


http_parser_factories: list[IHTTPParserFactory] = [
    H11HTTPParserFactory(h11),
    HTTPToolsParserFactory(httptools),
]

http_serializer_factories: list[IHTTPSerializerFactory] = [
    HTTPBaseSerializerFactory(),
]
websocket_parser_factories: list[IWebsocketParserFactory] = [
    WSProtoWebsocketParserFactory(wsproto),
]
websocket_serializer_factories: list[IWebsocketSerializerFactory] = [
    WSProtoWebsocketSerializerFactory(wsproto),
]
