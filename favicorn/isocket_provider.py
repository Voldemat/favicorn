import socket
from abc import ABC, abstractmethod
from typing import Literal


INET_FAMILY = (
    Literal[socket.AddressFamily.AF_INET]
    | Literal[socket.AddressFamily.AF_INET6]
    | Literal[socket.AddressFamily.AF_UNSPEC]
)


class ISocketProvider(ABC):
    @abstractmethod
    def acquire(self) -> socket.socket:
        raise NotImplementedError

    @abstractmethod
    def cleanup(self) -> None:
        raise NotImplementedError
