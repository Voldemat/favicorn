from favicorn.socket_providers import UnixSocketProvider


def test_unix_socket_provider() -> None:
    unix_provider = UnixSocketProvider(
        path="./server.sock", reuse_address=True
    )
    try:
        sock = unix_provider.acquire()
        assert id(sock) == id(unix_provider.acquire())
        assert sock.getsockname() == "./server.sock"
    finally:
        unix_provider.cleanup()
