from hiero_sdk_python import PrivateKey

from ..utils.encoding import bytes_to_b64
from .hcs_message import HcsMessage

MESSAGE_KEY = "message"
SIGNATURE_KEY = "signature"


class HcsMessageEnvelope(HcsMessage):
    _message_class: type[HcsMessage]

    def __init__(self, message: HcsMessage, signature: str | None = None):
        if isinstance(message, HcsMessageEnvelope):
            raise Exception("Nested HCS message envelopes are not allowed")

        self.message = message
        self.signature = signature

    def sign(self, signing_key: PrivateKey):
        if self.signature:
            raise Exception("Message is already signed")

        message_bytes = self.message.to_json().encode()
        signature_bytes = bytes(signing_key.sign(message_bytes))

        self.signature = bytes_to_b64(signature_bytes)

    def is_valid(self, topic_id: str | None = None) -> bool:
        if not self.message or not self.signature:
            return False

        return self.message.is_valid(topic_id)

    def get_payload_hash(self) -> str:
        return self.signature if self.signature else super().get_payload_hash()

    @classmethod
    def from_json_payload(cls, payload: dict):
        message = cls._message_class.from_json_payload(payload[MESSAGE_KEY])
        signature = payload[SIGNATURE_KEY]

        return cls(message, signature)

    def get_json_payload(self):
        result: dict = {MESSAGE_KEY: self.message.get_json_payload()}

        if self.signature:
            result[SIGNATURE_KEY] = self.signature

        return result
