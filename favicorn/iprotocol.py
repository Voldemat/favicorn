import asyncio
from abc import abstractmethod

from asgiref.typing import ASGI3Application

from .iglobal_state import IGlobalState


class IProtocol(asyncio.Protocol):
    @abstractmethod
    def __init__(
        self, global_state: IGlobalState, app: ASGI3Application
    ) -> None:
        raise NotImplementedError
