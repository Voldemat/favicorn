import socket

from favicorn.socket_providers import InetSocketProvider


def test_inet_socket_provider() -> None:
    inet_provider = InetSocketProvider(
        host="127.0.0.1", port=8000, reuse_address=True
    )
    sock = inet_provider.acquire()
    assert id(sock) == id(inet_provider.acquire())
    assert (
        sock.getsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
        )
        == socket.SO_REUSEADDR
    )
    assert sock.getsockname() == ("127.0.0.1", 8000)
