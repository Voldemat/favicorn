from types import ModuleType

from favicorn.i.protocols.websocket.parser import (
    IWebsocketParser,
    IWebsocketParserFactory,
)


class WSProtoWebsocketParser(IWebsocketParser):
    def __init__(self, wsproto: ModuleType) -> None:
        self.wsproto = wsproto
        self.parser = wsproto.frame_protocol.FrameProtocol(
            client=False, extensions=[]
        )
        self.Opcode = wsproto.frame_protocol.Opcode

    def feed_data(self, data: bytes) -> None:
        self.parser.receive_bytes(data)

    def get_data(self) -> str | bytes | int | None:
        for event in self.parser.received_frames():
            if event.opcode in (self.Opcode.BINARY, self.Opcode.TEXT):
                return event.payload  # type: ignore[no-any-return]
            raise ValueError(f"Unhandled event {event}")
        return None


class WSProtoWebsocketParserFactory(IWebsocketParserFactory):
    wsproto: ModuleType

    def __init__(self, wsproto: ModuleType) -> None:
        self.wsproto = wsproto

    def build(self) -> IWebsocketParser:
        return WSProtoWebsocketParser(self.wsproto)
