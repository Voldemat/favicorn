from abc import ABC, abstractmethod

from .icontroller import IHTTPController


class IHTTPControllerFactory(ABC):
    @abstractmethod
    def build(self, client: tuple[str, int] | None) -> IHTTPController:
        raise NotImplementedError
