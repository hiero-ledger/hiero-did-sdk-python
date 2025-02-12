import pytest

from hiero_did_sdk_python.did.hcs.events.hcs_did_event import HcsDidEventTarget
from hiero_did_sdk_python.did.hcs.events.verification_relationship import HcsDidUpdateVerificationRelationshipEvent

from ...common import IDENTIFIER_2


@pytest.fixture
def event(test_key):
    return HcsDidUpdateVerificationRelationshipEvent(
        f"{IDENTIFIER_2}#key-1", test_key.public_key, IDENTIFIER_2, "authentication", test_key.key_type
    )


class TestHcsDidUpdateVerificationRelationshipEvent:
    def test_target(self, event):
        """targets verificationMethod"""
        assert event.event_target == HcsDidEventTarget.VERIFICATION_RELATIONSHIP

    def test_throws_id_not_valid(self, test_key):
        """throws error if id is not valid"""
        with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#key-{number}"):
            HcsDidUpdateVerificationRelationshipEvent(
                IDENTIFIER_2, test_key.public_key, IDENTIFIER_2, "authentication", test_key.key_type
            )

    def test_get_id(self, event):
        """returns id passed via constructor"""
        assert event.id_ == f"{IDENTIFIER_2}#key-1"

    def test_get_type(self, event, test_key):
        """returns type passed via constructor"""
        assert event.type_ == test_key.key_type

    def test_get_relationship_type(self, event):
        """returns relationshipType passed via constructor"""
        assert event.relationship_type == "authentication"

    def test_get_controller(self, event):
        """reeturns type passed via constructor"""
        assert event.controller == IDENTIFIER_2
