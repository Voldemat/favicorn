import asyncio
import time
from email.utils import formatdate


def is_ssl(transport: asyncio.Transport) -> bool:
    return transport.get_extra_info("sslcontext") is None


def get_remote_addr(transport: asyncio.Transport) -> tuple[str, int] | None:
    if socket_info := transport.get_extra_info("socket"):
        if info := socket_info.getpeername():
            return (str(info[0]), int(info[1]))
    if info := transport.get_extra_info("peername"):
        return (str(info[0]), int(info[1]))
    return None


def get_date_in_email_format() -> str:
    return formatdate(time.time(), usegmt=True)
