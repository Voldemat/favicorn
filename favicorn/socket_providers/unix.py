import os
import socket

from favicorn.i.socket_provider import ISocketProvider


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

    def get_addr(self) -> str:
        return self.path
