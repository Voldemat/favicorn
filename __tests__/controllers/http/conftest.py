from favicorn.i.http.parser import IHTTPParserFactory
from favicorn.i.http.serializer import IHTTPSerializerFactory
from favicorn.i.websocket.parser import IWebsocketParserFactory
from favicorn.i.websocket.serializer import IWebsocketSerializerFactory
from favicorn.parsers.http import (
    H11HTTPParserFactory,
    HTTPToolsParserFactory,
)
from favicorn.parsers.websocket import (
    WSProtoWebsocketParserFactory,
)
from favicorn.serializers.http import HTTPBaseSerializerFactory
from favicorn.serializers.websocket import WSProtoWebsocketSerializerFactory

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
