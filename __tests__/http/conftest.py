from favicorn.controllers.http.iparser import IHTTPParserFactory
from favicorn.controllers.http.iserializer import IHTTPSerializerFactory
from favicorn.controllers.http.parsers import (
    H11HTTPParserFactory,
    HTTPToolsParserFactory,
)
from favicorn.controllers.http.serializers import HTTPBaseSerializerFactory
from favicorn.event_buses import DequeEventBusFactory
from favicorn.i.event_bus import IEventBusFactory

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
