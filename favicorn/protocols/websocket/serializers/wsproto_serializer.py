import base64
import hashlib
from types import ModuleType

from favicorn.i.protocols.websocket.serializer import (
    IWebsocketSerializer,
    IWebsocketSerializerFactory,
)


ACCEPT_GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class WSProtoWebsocketSerializer(IWebsocketSerializer):
    def __init__(self, wsproto: ModuleType, is_client: bool) -> None:
        self.wsproto = wsproto
        self.serializer = wsproto.frame_protocol.FrameProtocol(
            client=is_client, extensions=[]
        )

    def create_accept_token(self, client_token: bytes) -> bytes:
        accept_token = client_token + ACCEPT_GUID
        accept_token = hashlib.sha1(accept_token).digest()
        return base64.b64encode(accept_token)

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
