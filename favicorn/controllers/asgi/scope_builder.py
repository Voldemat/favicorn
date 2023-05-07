from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from asgiref.typing import (
        WWWScope,
        HTTPScope,
        Scope,
        WebSocketScope,
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
    ) -> "WWWScope":
        base_scope = {
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
        if metadata.is_websocket():
            return cast(
                "WebSocketScope",
                {**base_scope, "type": "websocket", "scheme": "ws"},
            )
        else:
            return cast(
                "HTTPScope", {**base_scope, "type": "http", "scheme": "http"}
            )

    def get_header(self, scope: "Scope", header: bytes) -> bytes | None:
        if scope["type"] == "lifespan":
            return None
        for header_name, value in scope["headers"]:
            if header_name != header:
                continue
            return value
        return None
