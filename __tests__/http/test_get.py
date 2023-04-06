from asgiref.typing import ASGIReceiveCallable, ASGISendCallable, WWWScope

import httpx

from ..conftest import serving_app


async def test_get() -> None:
    async def app(
        scope: WWWScope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        assert scope["type"] == "http"
        assert scope["http_version"] == "1.1"
        assert scope["method"] == "GET"
        assert scope["path"] == "/check"
        event = await receive()
        assert event["type"] == "http.request"
        assert event["body"] == b""
        assert event["more_body"] is False
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [],
                "trailers": False,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"Hello world",
                "more_body": False,
            }
        )

    with serving_app(app, host="localhost", port=8000):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/check", headers={"Connection": "close"}
            )
            assert response.status_code == 200, response.text
            assert response.text == "Hello world"


async def test_get_with_internal_server_error() -> None:
    class TestException(BaseException):
        pass

    async def app(
        scope: WWWScope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        raise TestException()

    with serving_app(
        app, host="localhost", port=8000, suppress_exceptions=(TestException,)
    ):
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000")
            assert response.status_code == 500, response.text
            assert response.text == "Internal Server Error"
