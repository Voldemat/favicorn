from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asgiref.typing import (
        HTTPScope,
    )

from favicorn.i.http.request_metadata import RequestMetadata


class ASGIScopeBuilder:
    def __init__(
        self,
        server: tuple[str, int | None] | None = None,
        root_path: str = "",
    ) -> None:
        self.server = server
        self.root_path = root_path

    def build(
        self, metadata: RequestMetadata, client: tuple[str, int] | None
    ) -> "HTTPScope":
        return {
            "type": "http",
            "scheme": "http",
            "path": metadata.path,
            "asgi": {"spec_version": "2.3", "version": "3.0"},
            "http_version": metadata.http_version,
            "raw_path": metadata.raw_path,
            "query_string": metadata.query_string or b"",
            "headers": metadata.headers,
            "root_path": self.root_path,
            "server": self.server,
            "client": client,
            "extensions": {},
            "method": metadata.method,
        }
