import asyncio
import os
import socket
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Type

from .http_protocol import HTTPProtocol

INET_FAMILY = (
    Literal[socket.AddressFamily.AF_INET]
    | Literal[socket.AddressFamily.AF_INET6]
    | Literal[socket.AddressFamily.AF_UNSPEC]
)


class IServerAddress(ABC):
    @abstractmethod
    def create_socket(self) -> socket.socket:
        raise NotImplementedError

    @abstractmethod
    def delete_socket(self, sock: socket.socket) -> None:
        raise NotImplementedError


@dataclass
class InetAddress(IServerAddress):
    host: str
    port: int
    family: INET_FAMILY = socket.AddressFamily.AF_UNSPEC

    def create_socket(self) -> socket.socket:
        sock = socket.socket(self.family, socket.SOCK_STREAM)
        self.configure_socket(sock)
        sock.bind((self.host, self.port))
        return sock

    def configure_socket(self, sock: socket.socket) -> None:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def delete_socket(self, _: socket.socket) -> None:
        pass


@dataclass
class UnixAddress(IServerAddress):
    path: str

    def create_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.configure_socket(sock)
        sock.bind(self.path)
        return sock

    def configure_socket(self, sock: socket.socket) -> None:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def delete_socket(self, sock: socket.socket) -> None:
        os.unlink(self.path)


class Server:
    address: IServerAddress
    protocol: Type[asyncio.Protocol]
    sock: socket.socket | None
    server: asyncio.Server | None

    def __init__(
        self,
        address: IServerAddress,
        protocol: Type[asyncio.Protocol] = HTTPProtocol,
    ) -> None:
        self.address = address
        self.protocol = protocol
        self.sock = None
        self.server = None

    async def init(self) -> None:
        loop = asyncio.get_event_loop()
        self.sock = self.address.create_socket()
        self.server = await loop.create_server(
            self.protocol,
            sock=self.sock,
            start_serving=False,
        )

    async def shutdown(self) -> None:
        if self.sock is not None:
            self.address.delete_socket(self.sock)

    async def serve(self) -> None:
        if self.server is None:
            raise ValueError("Server is not initialized yet")
        await self.server.serve_forever()
