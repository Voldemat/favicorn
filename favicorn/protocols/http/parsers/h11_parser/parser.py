from types import ModuleType
from typing import Iterable

from favicorn.i.protocols.http.parser import (
    HTTPParsingException,
    IHTTPParser,
    IHTTPParserFactory,
)
from favicorn.i.protocols.http.request_metadata import RequestMetadata


class H11HTTPParser(IHTTPParser):
    error: HTTPParsingException | None
    path: str | None
    method: str | None
    headers: list[tuple[bytes, bytes]]
    http_version: str | None
    query_string: bytes | None
    body: bytes | None
    connection_header: str | None
    more_body: bool

    def __init__(self, h11: ModuleType) -> None:
        self.h11 = h11
        self.parser = h11.Connection(our_role=h11.SERVER)
        self.error = None
        self.path = None
        self.body = None
        self.method = None
        self.headers = []
        self.http_version = None
        self.query_string = None
        self.connection_header = None
        self.more_body = True

    def feed_data(self, data: bytes) -> None:
        self.parser.receive_data(data)
        self.process_event()

    def process_event(self) -> None:
        try:
            event = self.parser.next_event()
        except self.h11.RemoteProtocolError as error:
            if str(error) == "Missing mandatory Host: header":
                self.error = HTTPParsingException("Host header is abscent")
            elif str(error) == "Found multiple Host: headers":
                self.error = HTTPParsingException("Host have multiple entries")
            else:
                self.error = HTTPParsingException(error)
            return
        if event is self.h11.NEED_DATA:
            return
        elif isinstance(event, self.h11.Request):
            self.set_path(event.target.decode())
            self.set_method(event.method.decode())
            self.set_headers(event.headers)
            self.set_http_version(event.http_version.decode())
        elif isinstance(event, self.h11.Data):
            self.set_body(event.data)
        elif isinstance(event, self.h11.EndOfMessage):
            self.more_body = False
            if self.body is None:
                self.set_body(b"")
            return
        return self.process_event()

    def set_path(self, path: str) -> None:
        if "?" in path:
            path, query = path.split("?")
            self.query_string = query.encode()
        self.path = path

    def set_method(self, method: str) -> None:
        self.method = method.upper()

    def set_headers(self, headers: Iterable[tuple[bytes, bytes]]) -> None:
        for header, value in map(
            lambda item: (
                item[0].lower(),
                item[1],
            ),
            headers,
        ):
            self.headers.append((header, value))
            if header == b"connection":
                self.connection_header = value.decode()

    def set_http_version(self, http_version: str) -> None:
        self.http_version = http_version

    def set_body(self, body: bytes) -> None:
        self.body = body

    def is_metadata_ready(self) -> bool:
        return (
            self.method is not None
            and self.path is not None
            and self.headers is not None
            and self.http_version is not None
        )

    def get_metadata(self) -> RequestMetadata:
        assert (
            self.method is not None
            and self.path is not None
            and self.headers is not None
            and self.http_version is not None
        )
        return RequestMetadata(
            path=self.path,
            method=self.method,
            headers=self.headers,
            raw_path=self.path.encode(),
            http_version=self.http_version,
            query_string=self.query_string,
        )

    def get_error(self) -> HTTPParsingException | None:
        return self.error

    def get_body(self) -> bytes | None:
        body = self.body
        self.body = None
        return body

    def is_more_body(self) -> bool:
        return self.more_body


class H11HTTPParserFactory(IHTTPParserFactory):
    h11: ModuleType

    def __init__(self, h11: ModuleType) -> None:
        self.h11 = h11

    def build(self) -> IHTTPParser:
        return H11HTTPParser(self.h11)
