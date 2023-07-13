from abc import ABC, abstractmethod

from .server import IServer


class IBuilder(ABC):
    @abstractmethod
    def build(self) -> IServer:
        pass
