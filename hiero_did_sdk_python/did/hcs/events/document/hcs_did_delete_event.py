from dataclasses import dataclass
from typing import ClassVar

from ..hcs_did_event import HcsDidEvent
from ..hcs_did_event_target import HcsDidEventTarget


@dataclass
class HcsDidDeleteEvent(HcsDidEvent):
    event_target: ClassVar[HcsDidEventTarget] = HcsDidEventTarget.DOCUMENT

    @classmethod
    def from_json_payload(cls, payload: dict):
        event_json = payload[cls.event_target]
        match event_json:
            case {}:
                return cls()
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return {self.event_target: {}}
