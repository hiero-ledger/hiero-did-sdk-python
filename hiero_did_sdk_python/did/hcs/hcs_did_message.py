import json
import time

from ...hcs import HcsMessage, HcsMessageEnvelope
from ...utils.encoding import b64_to_str, str_to_b64
from ..did_document_operation import DidDocumentOperation
from ..utils import parse_identifier
from .events.document.hcs_did_create_did_document_event import HcsDidCreateDidDocumentEvent
from .events.document.hcs_did_delete_event import HcsDidDeleteEvent
from .events.hcs_did_event import HcsDidEvent
from .events.hcs_did_event_target import HcsDidEventTarget
from .events.owner.hcs_did_update_did_owner_event import HcsDidUpdateDidOwnerEvent
from .events.service.hcs_did_revoke_service_event import HcsDidRevokeServiceEvent
from .events.service.hcs_did_update_service_event import HcsDidUpdateServiceEvent
from .events.verification_method.hcs_did_revoke_verification_method_event import HcsDidRevokeVerificationMethodEvent
from .events.verification_method.hcs_did_update_verification_method_event import HcsDidUpdateVerificationMethodEvent
from .events.verification_relationship.hcs_did_revoke_verification_relationship_event import (
    HcsDidRevokeVerificationRelationshipEvent,
)
from .events.verification_relationship.hcs_did_update_verification_relationship_event import (
    HcsDidUpdateVerificationRelationshipEvent,
)


def _parse_hcs_did_event(event_base64: str, operation: DidDocumentOperation) -> HcsDidEvent:  # noqa: C901
    event_json = b64_to_str(event_base64)

    # Retrieve the first key in dict - event target
    event_target = next(iter(json.loads(event_json)))

    if not event_target:
        raise Exception("Event target is not defined")

    match operation:
        case DidDocumentOperation.CREATE | DidDocumentOperation.UPDATE:
            match event_target:
                case HcsDidEventTarget.DID_DOCUMENT:
                    return HcsDidCreateDidDocumentEvent.from_json(event_json)
                case HcsDidEventTarget.DID_OWNER:
                    return HcsDidUpdateDidOwnerEvent.from_json(event_json)
                case HcsDidEventTarget.SERVICE:
                    return HcsDidUpdateServiceEvent.from_json(event_json)
                case HcsDidEventTarget.VERIFICATION_METHOD:
                    return HcsDidUpdateVerificationMethodEvent.from_json(event_json)
                case HcsDidEventTarget.VERIFICATION_RELATIONSHIP:
                    return HcsDidUpdateVerificationRelationshipEvent.from_json(event_json)
        case DidDocumentOperation.REVOKE:
            match event_target:
                case HcsDidEventTarget.SERVICE:
                    return HcsDidRevokeServiceEvent.from_json(event_json)
                case HcsDidEventTarget.VERIFICATION_METHOD:
                    return HcsDidRevokeVerificationMethodEvent.from_json(event_json)
                case HcsDidEventTarget.VERIFICATION_RELATIONSHIP:
                    return HcsDidRevokeVerificationRelationshipEvent.from_json(event_json)
        case DidDocumentOperation.DELETE:
            match event_target:
                case HcsDidEventTarget.DOCUMENT:
                    return HcsDidDeleteEvent.from_json(event_json)

    raise Exception(f"Error on parsing HcsDidEvent: {operation} - {event_target} is not supported")


class HcsDidMessage(HcsMessage):
    def __init__(self, operation: DidDocumentOperation, did: str, event: HcsDidEvent, timestamp: float = time.time()):
        self.operation = operation
        self.did = did
        self.event = event
        self.timestamp = timestamp

    @property
    def event_base64(self):
        return str_to_b64(self.event.to_json())

    def is_valid(self, topic_id: str | None = None) -> bool:
        if not self.did or not self.event or not self.operation:
            return False

        try:
            did_topic_id = parse_identifier(self.did).topic_id

            # Verify that the message was sent to the right topic, if the DID contain the topic
            if topic_id and did_topic_id and topic_id != did_topic_id:
                return False
        except Exception:
            return False

        return True

    @classmethod
    def from_json_payload(cls, payload: dict):
        match payload:
            case {"timestamp": timestamp, "operation": operation, "did": did, "event": event_base64}:
                parsed_event = _parse_hcs_did_event(event_base64, operation)
                return cls(operation=operation, did=did, event=parsed_event, timestamp=timestamp)
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return {
            "timestamp": self.timestamp,
            "operation": self.operation.value,
            "did": self.did,
            "event": self.event_base64,
        }


class HcsDidMessageEnvelope(HcsMessageEnvelope):
    _message_class = HcsDidMessage
