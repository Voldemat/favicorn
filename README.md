# Favicorn
![CI](https://github.com/Voldemat/favicorn/actions/workflows/python-package.yml/badge.svg)
[![PyPI version](https://badge.fury.io/py/favicorn.svg)](https://badge.fury.io/py/favicorn)
[![codecov](https://codecov.io/github/Voldemat/favicorn/branch/main/graph/badge.svg?token=7X60C005I2)](https://codecov.io/github/Voldemat/favicorn)


## Installation
```bash
pip3 install favicorn 
```

## ASGI Usage


```bash
pip3 install httptools
```
main.py
```python
import asyncio
import logging

from favicorn import ASGIFavicornBuilder


logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s"
)
async def app(scope, receive, send) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"Content-Length", b"0")],
        }
    )
    await send({"type": "http.response.body", "body": b"", "more_body": False})
s = ASGIFavicornBuilder(
    app=app,
    http_parser_impl="httptools",
).build()

async def main() -> None:
    await s.init()
    try:
        await s.serve_forever()
    finally:
        await s.close()

asyncio.run(main())
```

```bash
python3 main.py
[2023-07-14 12:37:14,979][INFO] Socket ('127.0.0.1', 8000) acquired successfully using <class 'favicorn.socket_providers.inet.InetSocketProvider'>
[2023-07-14 12:37:14,979][INFO] Serve forever...
```

## ASGI Usage with websockets
```bash
pip3 install httptools wsproto
```
main.py
```python
import asyncio
import logging

from favicorn import ASGIFavicornBuilder


logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s"
)

async def app(scope, receive, send) -> None:
    await send({"type": "websocket.accept"})
    msg = await receive()
    await send({"type": "websocket.send", "bytes": b"Something", "text": None})
    await send({"type": "websocket.close", "code": 1000})

s = ASGIFavicornBuilder(
    app=app,
    http_parser_impl="httptools",
    ws_impl='wsproto'
).build()

async def main() -> None:
    await s.init()
    try:
        await s.serve_forever()
    finally:
        await s.close()

asyncio.run(main())
```

```bash
python3 main.py
[2023-07-14 12:37:14,979][INFO] Socket ('127.0.0.1', 8000) acquired successfully using <class 'favicorn.socket_providers.inet.InetSocketProvider'>
[2023-07-14 12:37:14,979][INFO] Serve forever...
```

