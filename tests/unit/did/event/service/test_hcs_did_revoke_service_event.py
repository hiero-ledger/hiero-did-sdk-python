import pytest

from hiero_did_sdk_python.did.hcs.events.service.hcs_did_revoke_service_event import HcsDidRevokeServiceEvent

from ...common import IDENTIFIER_2


@pytest.fixture()
def event():
    return HcsDidRevokeServiceEvent(f"{IDENTIFIER_2}#service-1")


class TestHcsDidRevokeServiceEvent:
    def test_throws_id_not_valid(self):
        """throws error if id is not valid"""
        with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#service-{number}"):
            HcsDidRevokeServiceEvent(IDENTIFIER_2)

    def test_get_id(self, event):
        """returns id passed via constructor"""
        assert event.id_ == f"{IDENTIFIER_2}#service-1"
