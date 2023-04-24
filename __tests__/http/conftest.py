from favicorn.connections.http.event_buses import HTTPDequeEventBusFactory
from favicorn.connections.http.ievent_bus import IHTTPEventBusFactory
from favicorn.connections.http.iparser import IHTTPParserFactory
from favicorn.connections.http.iserializer import IHTTPSerializerFactory
from favicorn.connections.http.parsers import (
    H11HTTPParserFactory,
    HTTPToolsParserFactory,
)
from favicorn.connections.http.serializers import HTTPBaseSerializerFactory

import h11

import httptools


parser_factories: list[IHTTPParserFactory] = [
    H11HTTPParserFactory(h11),
    HTTPToolsParserFactory(httptools),
]
event_bus_factories: list[IHTTPEventBusFactory] = [
    HTTPDequeEventBusFactory(),
]
serializer_factories: list[IHTTPSerializerFactory] = [
    HTTPBaseSerializerFactory(),
]
