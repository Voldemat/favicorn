from dataclasses import dataclass
from typing import Iterable


@dataclass
class RequestMetadata:
    path: str
    method: str
    raw_path: bytes
    http_version: str
    query_string: bytes | None
    headers: Iterable[tuple[bytes, bytes]]

    def is_keepalive(self) -> bool:
        if connection_header := next(
            filter(lambda h: h[0] == b"connection", self.headers), None
        ):
            _, value = connection_header
            if value == b"keep-alive":
                return True
            elif value == b"close":
                return False
        if self.http_version == "1.0":
            return False
        return True

    def is_websocket(self) -> bool:
        for header, value in self.headers:
            if header != b"upgrade":
                continue
            return value == b"websocket"
        return False
