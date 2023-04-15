import socket

from favicorn.socket_providers import UnixSocketProvider


def test_unix_socket_provider() -> None:
    unix_provider = UnixSocketProvider(
        path="./server.sock", reuse_address=True
    )
    try:
        sock = unix_provider.acquire()
        assert id(sock) == id(unix_provider.acquire())
        assert (
            sock.getsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
            )
            == socket.SO_REUSEADDR
        )
        assert sock.getsockname() == "./server.sock"
    finally:
        unix_provider.cleanup()
