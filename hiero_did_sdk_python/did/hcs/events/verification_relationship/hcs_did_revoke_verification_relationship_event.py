from dataclasses import dataclass
from typing import ClassVar

from ....types import VerificationRelationshipType
from ....utils import is_key_event_id_valid
from ..hcs_did_event import HcsDidEvent
from ..hcs_did_event_target import HcsDidEventTarget


@dataclass
class HcsDidRevokeVerificationRelationshipEvent(HcsDidEvent):
    id_: str
    relationship_type: VerificationRelationshipType
    event_target: ClassVar[HcsDidEventTarget] = HcsDidEventTarget.VERIFICATION_RELATIONSHIP

    def __post_init__(self):
        if not is_key_event_id_valid(self.id_):
            raise Exception("Event ID is invalid. Expected format: {did}#key-{number}")

    @classmethod
    def from_json_payload(cls, payload: dict):
        event_json = payload[cls.event_target]
        match event_json:
            case {"id": id_, "relationshipType": relationship_type}:
                return cls(id_=id_, relationship_type=relationship_type)
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return {self.event_target: {"id": self.id_, "relationshipType": self.relationship_type}}
