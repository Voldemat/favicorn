import asyncio
from ipaddress import IPv4Address
from typing import AsyncGenerator

from httpx import AsyncClient

import pytest

from favicorn_core import Server


@pytest.fixture
def server() -> Server:
    return Server(IPv4Address('0.0.0.0'), 8000)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(base_url="http://0.0.0.0:8000/") as c:
        yield c


def test_invalid_port() -> None:
    with pytest.raises(RuntimeError) as exc:
        Server(IPv4Address('127.0.0.1'), 30)
    assert str(exc.value) == "Error binding socket: Permission denied"


async def test_server(server: Server, client: AsyncClient) -> None:
    future = server.receive()
    assert isinstance(future, asyncio.Future)
    client_task = asyncio.create_task(client.get('/home'))
    print(client_task)

    results = await asyncio.gather(client_task, future)
    print(results)
