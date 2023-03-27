import socket
from abc import ABC, abstractmethod


class ISocketProvider(ABC):
    @abstractmethod
    def acquire(self) -> socket.socket:
        raise NotImplementedError

    @abstractmethod
    def cleanup(self) -> None:
        raise NotImplementedError
