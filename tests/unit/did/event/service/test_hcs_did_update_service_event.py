import pytest

from hiero_did_sdk_python.did.hcs.events.hcs_did_event import HcsDidEventTarget
from hiero_did_sdk_python.did.hcs.events.service import HcsDidUpdateServiceEvent

from ...common import IDENTIFIER_2


@pytest.fixture
def event():
    return HcsDidUpdateServiceEvent(f"{IDENTIFIER_2}#service-1", "DIDCommMessaging", "https://vc.test.service.com")


class TestHcsDidUpdateServiceEvent:
    def test_target(self, event):
        """targets Service"""
        assert event.event_target == HcsDidEventTarget.SERVICE

    def test_throws_id_not_valid(self):
        """throws error if id is not valid"""
        with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#service-{number}"):
            HcsDidUpdateServiceEvent(IDENTIFIER_2, "DIDCommMessaging", "https://vs.test.service.com")

    def test_get_id(self, event):
        """returns id passed via constructor"""
        assert event.id_ == f"{IDENTIFIER_2}#service-1"

    def test_get_type(self, event):
        """returns type passed via constructor"""
        assert event.type_ == "DIDCommMessaging"

    def test_get_service_endpoint(self, event):
        """returns endpoint passed via constructor"""
        assert event.service_endpoint == "https://vc.test.service.com"
