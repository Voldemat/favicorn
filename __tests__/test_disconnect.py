import socket
import time

from asgiref.typing import ASGIReceiveCallable, ASGISendCallable, HTTPScope

from .conftest import serving_app


async def test_disconnect() -> None:
    async def app(
        scope: HTTPScope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        assert scope["method"] == "GET"
        assert scope["path"] == "/"
        await receive()
        disconnect_event = await receive()
        assert disconnect_event["type"] == "http.disconnect"

    host = "0.0.0.0"
    port = 8000
    with serving_app(app, host=host, port=port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((host, port))
            sock.sendall(b"GET / HTTP/1.1\n\n")
            time.sleep(0.01)
            sock.close()
