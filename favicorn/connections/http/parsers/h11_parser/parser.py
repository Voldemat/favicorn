from types import ModuleType
from typing import Iterable

from favicorn.connections.http.iparser import (
    HTTPParsingException,
    IHTTPParser,
    IHTTPParserFactory,
)
from favicorn.connections.http.request_metadata import RequestMetadata


class H11HTTPParser(IHTTPParser):
    error: HTTPParsingException | None
    path: str | None
    method: str | None
    headers: Iterable[tuple[bytes, bytes]] | None
    http_version: str | None
    query_string: bytes | None
    keepalive: bool
    body: bytes | None

    def __init__(self, h11: ModuleType) -> None:
        self.h11 = h11
        self.parser = h11.Connection(our_role=h11.SERVER)
        self.error = None
        self.path = None
        self.method = None
        self.headers = None
        self.http_version = None
        self.query_string = None
        self.keepalive = True
        self.body = None

    def feed_data(self, data: bytes) -> None:
        self.parser.receive_data(data)
        self.process_event()

    def process_event(self) -> None:
        try:
            event = self.parser.next_event()
        except self.h11.RemoteProtocolError as error:
            if str(error) == "Missing mandatory Host: header":
                self.error = HTTPParsingException("Host header is abscent")
            else:
                self.error = HTTPParsingException(error)
            return
        if event is self.h11.NEED_DATA:
            return
        if isinstance(event, self.h11.Request):
            full_path = event.target.decode()
            if "?" in full_path:
                self.path, query = full_path.split("?")
                self.query_string = query.encode()
            else:
                self.path = full_path
            self.method = event.method.decode()
            self.headers = list(
                map(
                    lambda item: (
                        item[0].decode().lower().encode(),
                        item[1].decode().lower().encode(),
                    ),
                    event.headers,
                )
            )
            self.http_version = event.http_version.decode()
            self.keepalive = self.http_version == "1.1"
            if connection_header := next(
                map(
                    lambda item: item[1].decode(),
                    filter(
                        lambda item: item[0] == b"connection", self.headers
                    ),
                ),
                None,
            ):
                self.keepalive = connection_header == "keep-alive"
        elif isinstance(event, self.h11.Data):
            self.body = event.data
        elif isinstance(event, self.h11.EndOfMessage):
            if self.body is None:
                self.body = b""
            return
        return self.process_event()

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
            is_keepalive=self.keepalive,
            http_version=self.http_version,
            query_string=self.query_string,
        )

    def has_error(self) -> bool:
        return self.error is not None

    def get_error(self) -> HTTPParsingException:
        assert self.error is not None
        return self.error

    def has_body(self) -> bool:
        return self.body is not None

    def get_body(self) -> bytes:
        assert self.body is not None
        body = self.body
        self.body = None
        return body

    def is_more_body(self) -> bool:
        return False

    def is_keepalive(self) -> bool:
        return self.http_version == "1.1"


class H11HTTPParserFactory(IHTTPParserFactory):
    h11: ModuleType

    def __init__(self, h11: ModuleType) -> None:
        self.h11 = h11

    def build(self) -> IHTTPParser:
        return H11HTTPParser(self.h11)
