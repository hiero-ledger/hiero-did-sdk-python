from dataclasses import dataclass
from typing import ClassVar

from ....types import DidServiceType
from ....utils import is_service_event_id_valid
from ..hcs_did_event import HcsDidEvent
from ..hcs_did_event_target import HcsDidEventTarget


@dataclass
class HcsDidUpdateServiceEvent(HcsDidEvent):
    id_: str
    type_: DidServiceType
    service_endpoint: str
    event_target: ClassVar[HcsDidEventTarget] = HcsDidEventTarget.SERVICE

    def __post_init__(self):
        if not is_service_event_id_valid(self.id_):
            raise Exception("Event ID is invalid. Expected format: {did}#service-{number}")

    def get_service_def(self):
        return {"id": self.id_, "type": self.type_, "serviceEndpoint": self.service_endpoint}

    @classmethod
    def from_json_payload(cls, payload: dict):
        event_json = payload[cls.event_target]
        match event_json:
            case {"id": id_, "type": type_, "serviceEndpoint": service_endpoint}:
                return cls(id_=id_, type_=type_, service_endpoint=service_endpoint)
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return {self.event_target: self.get_service_def()}
