from favicorn.i.http.parser import IHTTPParserFactory
from favicorn.i.http.serializer import IHTTPSerializerFactory
from favicorn.parsers.http import (
    H11HTTPParserFactory,
    HTTPToolsParserFactory,
)
from favicorn.serializers.http import HTTPBaseSerializerFactory

import h11

import httptools


parser_factories: list[IHTTPParserFactory] = [
    H11HTTPParserFactory(h11),
    HTTPToolsParserFactory(httptools),
]

serializer_factories: list[IHTTPSerializerFactory] = [
    HTTPBaseSerializerFactory(),
]
