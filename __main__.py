import asyncio

from favicorn.server import Server, UnixAddress


def main() -> None:
    server = Server(address=UnixAddress(path="./server.sock"))
    loop = asyncio.new_event_loop()
    loop.run_until_complete(server.init())
    try:
        loop.run_until_complete(server.serve())
    finally:
        loop.run_until_complete(server.shutdown())


if __name__ == "__main__":
    main()
