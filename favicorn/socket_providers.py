import os
import socket
from typing import Literal

from .isocket_provider import ISocketProvider


INET_FAMILY = (
    Literal[socket.AddressFamily.AF_INET]
    | Literal[socket.AddressFamily.AF_INET6]
)


class InetSocketProvider(ISocketProvider):
    host: str
    port: int
    family: INET_FAMILY
    sock: socket.socket | None
    reuse_address: bool

    def __init__(
        self,
        host: str,
        port: int,
        family: INET_FAMILY = socket.AddressFamily.AF_INET,
        reuse_address: bool = False,
    ) -> None:
        self.host = host
        self.port = port
        self.family = family
        self.sock = None
        self.reuse_address = reuse_address

    def acquire(self) -> socket.socket:
        if self.sock is None:
            self.sock = self.create_socket()
        return self.sock

    def create_socket(self) -> socket.socket:
        sock = socket.socket(self.family, socket.SOCK_STREAM)
        self.configure_socket(sock)
        sock.bind((self.host, self.port))
        return sock

    def configure_socket(self, sock: socket.socket) -> None:
        sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, int(self.reuse_address)
        )

    def cleanup(self) -> None:
        pass

    def get_addr(self) -> tuple[str, int] | None:
        return (self.host, self.port)


class UnixSocketProvider(ISocketProvider):
    path: str
    reuse_address: bool
    sock: socket.socket | None

    def __init__(self, path: str, reuse_address: bool = False) -> None:
        self.path = path
        self.sock = None
        self.reuse_address = reuse_address

    def acquire(self) -> socket.socket:
        if self.sock is not None:
            return self.sock
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.configure_socket(self.sock)
        self.sock.bind(self.path)
        return self.sock

    def configure_socket(self, sock: socket.socket) -> None:
        sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, int(self.reuse_address)
        )

    def cleanup(self) -> None:
        os.unlink(self.path)

    def get_addr(self) -> tuple[str, int] | None:
        return None
