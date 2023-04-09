import asyncio


def get_remote_addr(transport: asyncio.StreamWriter) -> tuple[str, int] | None:
    if socket_info := transport.get_extra_info("socket"):
        if info := socket_info.getpeername():
            return (str(info[0]), int(info[1]))
    if info := transport.get_extra_info("peername"):
        return (str(info[0]), int(info[1]))
    return None
