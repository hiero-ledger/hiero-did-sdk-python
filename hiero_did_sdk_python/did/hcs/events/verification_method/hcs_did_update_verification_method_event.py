from dataclasses import dataclass
from typing import ClassVar

from hiero_sdk_python import PublicKey

from .....utils.encoding import b58_to_bytes, bytes_to_b58
from ....types import SupportedKeyType
from ....utils import is_key_event_id_valid
from ..hcs_did_event import HcsDidEvent
from ..hcs_did_event_target import HcsDidEventTarget


@dataclass
class HcsDidUpdateVerificationMethodEvent(HcsDidEvent):
    id_: str
    controller: str
    public_key: PublicKey
    type_: SupportedKeyType
    event_target: ClassVar[HcsDidEventTarget] = HcsDidEventTarget.VERIFICATION_METHOD

    def __post_init__(self):
        if not is_key_event_id_valid(self.id_):
            raise Exception("Event ID is invalid. Expected format: {did}#key-{number}")

    def get_verification_method_def(self):
        return {
            "id": self.id_,
            "type": self.type_,
            "controller": self.controller,
            "publicKeyBase58": bytes_to_b58(self.public_key.to_bytes_raw()),
        }

    @classmethod
    def from_json_payload(cls, payload: dict):
        event_json = payload[cls.event_target]
        match event_json:
            case {"id": id_, "type": type_, "controller": controller, "publicKeyBase58": public_key_base58}:
                public_key = PublicKey.from_bytes(b58_to_bytes(public_key_base58))
                return cls(id_=id_, type_=type_, controller=controller, public_key=public_key)
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return {self.event_target: self.get_verification_method_def()}
