from favicorn.connections.http.event_buses import DequeEventBusFactory
from favicorn.connections.http.ievent_bus import IEventBusFactory
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
event_bus_factories: list[IEventBusFactory] = [
    DequeEventBusFactory(),
]
serializer_factories: list[IHTTPSerializerFactory] = [
    HTTPBaseSerializerFactory(),
]
