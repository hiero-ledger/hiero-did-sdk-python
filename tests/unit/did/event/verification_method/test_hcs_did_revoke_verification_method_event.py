import pytest

from hiero_did_sdk_python.did.hcs.events.owner.hcs_did_update_did_owner_event import HcsDidEventTarget
from hiero_did_sdk_python.did.hcs.events.verification_method.hcs_did_revoke_verification_method_event import (
    HcsDidRevokeVerificationMethodEvent,
)

from ...common import IDENTIFIER_2


@pytest.fixture
def event():
    return HcsDidRevokeVerificationMethodEvent(f"{IDENTIFIER_2}#key-1")


class TestHcsDidRevokeVerificationMethodEvent:
    def test_target(self, event):
        """targets verificationMethod"""
        assert event.event_target == HcsDidEventTarget.VERIFICATION_METHOD

    def test_throws_if_id_null(self):
        """throws error if id is null"""
        with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#key-{number}"):
            HcsDidRevokeVerificationMethodEvent("")

    def test_throws_if_id_not_valid(self):
        """throws error if id is not valid"""
        with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#key-{number}"):
            HcsDidRevokeVerificationMethodEvent(IDENTIFIER_2)

    def test_get_id(self, event):
        """returns id passed via constructor"""
        assert event.id_ == f"{IDENTIFIER_2}#key-1"
