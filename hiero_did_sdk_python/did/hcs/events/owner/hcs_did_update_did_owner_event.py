from dataclasses import dataclass
from typing import ClassVar

from hiero_sdk_python import PublicKey

from .....did.types import SupportedKeyType
from .....utils.encoding import b58_to_bytes, bytes_to_b58
from ....utils import is_valid_did
from ..hcs_did_event import HcsDidEvent
from ..hcs_did_event_target import HcsDidEventTarget


@dataclass
class HcsDidUpdateDidOwnerEvent(HcsDidEvent):
    id_: str
    controller: str
    public_key: PublicKey
    type_: SupportedKeyType
    event_target: ClassVar[HcsDidEventTarget] = HcsDidEventTarget.DID_OWNER

    def __post_init__(self):
        if not is_valid_did(self.id_):
            raise Exception("Event ID is invalid. Expected Hedera DID format")

    def get_owner_def(self):
        return {
            "id": self.id_,
            "type": self.type_,
            "controller": self.controller,
            "publicKeyBase58": bytes_to_b58(self.public_key.to_bytes_raw()),
        }

    def get_controller_verification_method(self):
        owner_def = self.get_owner_def()
        return {
            **owner_def,
            "id": f"{owner_def["id"]}#did-root-key",
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

    def get_json_payload(self) -> dict:
        return {self.event_target: self.get_owner_def()}
