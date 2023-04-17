from types import ModuleType

from favicorn.connections.http.iparser import IHTTPParser, IHTTPParserFactory

from .parser import HTTPToolsParser


class HTTPToolsParserFactory(IHTTPParserFactory):
    def __init__(self, httptools: ModuleType) -> None:
        self.httptools = httptools

    def build(self) -> IHTTPParser:
        return HTTPToolsParser(self.httptools)
