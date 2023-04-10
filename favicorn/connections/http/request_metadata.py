from dataclasses import dataclass
from typing import Iterable


@dataclass
class RequestMetadata:
    path: str
    method: str
    raw_path: bytes
    http_version: str
    query_string: bytes
    headers: Iterable[tuple[bytes, bytes]]
