from dataclasses import dataclass
from typing import Iterable


@dataclass
class RequestMetadata:
    path: str
    method: str
    raw_path: bytes
    http_version: str
    is_keepalive: bool
    query_string: bytes | None
    headers: Iterable[tuple[bytes, bytes]]
