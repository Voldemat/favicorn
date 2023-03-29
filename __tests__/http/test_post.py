import json

from asgiref.typing import ASGIReceiveCallable, ASGISendCallable, HTTPScope

from httpx import AsyncClient

from ..conftest import serving_app


async def test_post_json() -> None:
    data = {"a": 1, "b": "c"}

    async def app(
        scope: HTTPScope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        assert scope["method"] == "POST"
        assert scope["path"] == "/data"
        body_event = await receive()
        assert body_event["type"] == "http.request"
        assert body_event["body"] == json.dumps(data).encode()
        assert body_event["more_body"] is False
        response_body = json.dumps({"status": "ok"}).encode()
        await send(
            {
                "type": "http.response.start",
                "headers": (
                    (b"Content-Type", b"application/json"),
                    (b"Content-Length", str(len(response_body)).encode()),
                ),
                "trailers": False,
                "status": 200,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": response_body,
                "more_body": False,
            }
        )

    with serving_app(app, host="localhost", port=8000):
        async with AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/data", json=data
            )
            assert response.status_code == 200, response.text
            res_json = response.json()
            assert res_json.get("status", None) == "ok", res_json
