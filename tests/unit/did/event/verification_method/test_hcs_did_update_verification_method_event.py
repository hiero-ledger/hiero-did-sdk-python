import pytest

from hiero_did_sdk_python.did.hcs.events.hcs_did_event_target import HcsDidEventTarget
from hiero_did_sdk_python.did.hcs.events.verification_method.hcs_did_update_verification_method_event import (
    HcsDidUpdateVerificationMethodEvent,
)

from ...common import IDENTIFIER_2


@pytest.fixture
def event(test_key):
    event = HcsDidUpdateVerificationMethodEvent(
        f"{IDENTIFIER_2}#key-1", IDENTIFIER_2, test_key.public_key, test_key.key_type
    )

    return event


class TestHcsDidUpdateVerificationMethodEvent:
    def test_targets_verification_method(self, event):
        """targets verificationMethod"""
        assert event.event_target == HcsDidEventTarget.VERIFICATION_METHOD

    def test_error_if_id_not_valid(self, test_key):
        """throws error if id is not valid"""
        with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#key-{number}"):
            HcsDidUpdateVerificationMethodEvent(IDENTIFIER_2, IDENTIFIER_2, test_key.public_key, test_key.key_type)

    def test_get_id(self, event):
        """returns id passed via constructor"""
        assert event.id_ == f"{IDENTIFIER_2}#key-1"

    def test_get_type(self, event, test_key):
        """returns type passed via constructor"""
        assert event.type_ == test_key.key_type

    def test_get_controller(self, event):
        """returns controller passed via constructor"""
        assert event.controller == IDENTIFIER_2

    def test_get_public_key_base58(self, event, test_key):
        """returns event data encoded in base64"""
        assert event.get_verification_method_def()["publicKeyBase58"] == test_key.public_key_base58

    def test_rebuild_event(self, test_key):
        """rebuilds HcsDidUpdateVerificationMethodEvent Object"""
        eventFromJson = HcsDidUpdateVerificationMethodEvent.from_json_payload({
            "VerificationMethod": {
                "controller": IDENTIFIER_2,
                "id": f"{IDENTIFIER_2}#key-1",
                "publicKeyBase58": test_key.public_key_base58,
                "type": test_key.key_type,
            }
        })

        assert isinstance(eventFromJson, HcsDidUpdateVerificationMethodEvent)

        assert eventFromJson.get_json_payload() == {
            "VerificationMethod": {
                "controller": IDENTIFIER_2,
                "id": f"{IDENTIFIER_2}#key-1",
                "publicKeyBase58": test_key.public_key_base58,
                "type": test_key.key_type,
            }
        }
