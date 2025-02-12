from dataclasses import dataclass
from typing import ClassVar

from ....utils import is_valid_did
from ..hcs_did_event import HcsDidEvent
from ..hcs_did_event_target import HcsDidEventTarget


@dataclass()
class HcsDidCreateDidDocumentEvent(HcsDidEvent):
    id_: str
    cid: str
    url: str | None = None
    type_: ClassVar[str] = HcsDidEventTarget.DID_DOCUMENT
    event_target: ClassVar[HcsDidEventTarget] = HcsDidEventTarget.DID_DOCUMENT

    def __post_init__(self):
        if not is_valid_did(self.id_):
            raise Exception("DID is invalid")

    @classmethod
    def from_json_payload(cls, payload: dict):
        event_json = payload[cls.event_target]
        match event_json:
            case {"id": id_, "type": _, "cid": cid, "url": url}:
                return cls(id_=id_, cid=cid, url=url)
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return {
            self.event_target: {
                "id": self.id_,
                "type": self.type_,
                "cid": self.cid,
                "url": self.url,
            }
        }
