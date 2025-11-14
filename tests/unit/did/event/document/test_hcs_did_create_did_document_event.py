import pytest

from hiero_did_sdk_python.did.hcs.events.document.hcs_did_create_did_document_event import HcsDidCreateDidDocumentEvent

from ...common import IDENTIFIER_2

CID = "QmaBcDeFgHiJkLmNoP"
URL = f"https://ipfs.io/ifs/{CID}"


@pytest.fixture()
def event():
    return HcsDidCreateDidDocumentEvent(IDENTIFIER_2, CID, URL)


class TestHcsDidCreateDidDocumentEvent:
    def test_error_not_valid(self):
        """throws error if id is not valid"""
        with pytest.raises(Exception, match="DID is invalid"):
            HcsDidCreateDidDocumentEvent("example", CID)

    def test_get_id(self, event):
        """returns the id that was passed via constructor"""
        assert event.id_ == IDENTIFIER_2

    def test_get_type(self, event):
        """returns DIDDocument"""
        assert event.type_ == "DIDDocument"

    def test_get_cid(self, event):
        """returns the cid that was passed via constructor"""
        assert event.cid == CID

    def test_get_url(self, event):
        """returns the url that was passed via constructor"""
        assert event.url == URL
