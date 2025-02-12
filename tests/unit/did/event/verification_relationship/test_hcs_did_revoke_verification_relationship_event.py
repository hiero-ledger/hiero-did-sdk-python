import pytest

from hiero_did_sdk_python.did.hcs.events.verification_relationship import HcsDidRevokeVerificationRelationshipEvent

from ...common import IDENTIFIER_2


@pytest.fixture
def event():
    return HcsDidRevokeVerificationRelationshipEvent(f"{IDENTIFIER_2}#key-1", "authentication")


class TestHcsDidRevokeVerificationRelationshipEvent:
    def test_throws_id_not_valid(self):
        """throws error if id is not valid"""
        with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#key-{number}"):
            HcsDidRevokeVerificationRelationshipEvent(IDENTIFIER_2, "authentication")

    def test_get_id(self, event):
        """returns id passed via constructor"""
        assert event.id_ == f"{IDENTIFIER_2}#key-1"

    def test_get_relationship_type(self, event):
        """returns relationshipType passed via constructor"""
        assert event.relationship_type == "authentication"
