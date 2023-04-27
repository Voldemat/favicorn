from dataclasses import dataclass


@dataclass
class HTTPControllerReceiveEvent:
    count: int | None
    timeout: float | None


@dataclass
class HTTPControllerSendEvent:
    data: bytes


HTTPControllerEvent = HTTPControllerReceiveEvent | HTTPControllerSendEvent
