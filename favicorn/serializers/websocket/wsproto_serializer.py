from types import ModuleType

from favicorn.i.websocket.serializer import (
    IWebsocketSerializer,
    IWebsocketSerializerFactory,
)


class WSProtoWebsocketSerializer(IWebsocketSerializer):
    def __init__(self, wsproto: ModuleType, is_client: bool) -> None:
        self.wsproto = wsproto
        self.serializer = wsproto.frame_protocol.FrameProtocol(
            client=is_client, extensions=[]
        )

    def serialize_data(self, data: bytes | str) -> bytes:
        opcode = (
            self.wsproto.frame_protocol.Opcode.TEXT
            if isinstance(data, str)
            else self.wsproto.frame_protocol.Opcode.BINARY
        )
        return self.serializer._serialize_frame(  # type: ignore[no-any-return]
            opcode=opcode, payload=data
        )

    def build_close_frame(self) -> bytes:
        return self.serializer._serialize_frame(  # type: ignore[no-any-return]
            opcode=self.wsproto.frame_protocol.Opcode.CLOSE,
        )


class WSProtoWebsocketSerializerFactory(IWebsocketSerializerFactory):
    wsproto: ModuleType

    def __init__(self, wsproto: ModuleType) -> None:
        self.wsproto = wsproto

    def build(self, is_client: bool = False) -> IWebsocketSerializer:
        return WSProtoWebsocketSerializer(
            wsproto=self.wsproto, is_client=is_client
        )
