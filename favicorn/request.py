from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Request:
    url: str
    method: str
    body: bytes | None
    headers: dict[str, str]


class RequestBuilder:
    _url: str | None
    _body: bytes | None
    _method: str | None
    _headers: dict[str, Any] | None

    def __init__(self) -> None:
        self._url = None
        self._body = None
        self._method = None
        self._headers = None

    def url(self, url: str) -> RequestBuilder:
        self._url = url
        return self

    def body(self, body: bytes) -> RequestBuilder:
        self._body = body
        return self

    def method(self, method: str) -> RequestBuilder:
        self._method = method
        return self

    def add_header(self, name: str, value: str) -> RequestBuilder:
        if self._headers is None:
            self._headers = {}

        self._headers[name] = value
        return self

    def build(self) -> Request:
        if self._url is None:
            raise ValueError("Url is not provided yet")
        if self._headers is None:
            raise ValueError("Headers is not provided yet")
        if self._method is None:
            raise ValueError("Method is not provided yet")
        return Request(
            url=self._url,
            body=self._body,
            headers=self._headers,
            method=self._method,
        )
