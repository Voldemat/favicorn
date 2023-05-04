import itertools
from dataclasses import dataclass
from typing import Iterable


@dataclass
class ResponseMetadata:
    status: int
    headers: Iterable[tuple[bytes, bytes]]

    def add_extra_headers(
        self, headers: Iterable[tuple[bytes, bytes]]
    ) -> None:
        self.headers = itertools.chain(self.headers, headers)
