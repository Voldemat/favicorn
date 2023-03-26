import asyncio
from abc import abstractmethod

from asgiref.typing import ASGI3Application


class IProtocol(asyncio.Protocol):
    @abstractmethod
    def __init__(self, app: ASGI3Application) -> None:
        raise NotImplementedError
