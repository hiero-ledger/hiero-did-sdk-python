import pytest

from hiero_did_sdk_python.did.did_document_operation import DidDocumentOperation
from hiero_did_sdk_python.did.hcs.hcs_did_message import _parse_hcs_did_event
from hiero_did_sdk_python.utils.encoding import str_to_b64


class TestHcsDidEventParser:
    def test_delete(self):
        """HcsDidDeleteEvent if operation is DELETE - ignores base64 data"""
        with pytest.raises(Exception, match="Error on parsing HcsDidEvent: delete - data is not supported"):
            _parse_hcs_did_event(str_to_b64('{"data":"data"}'), DidDocumentOperation.DELETE)

    def test_operation_not_found(self):
        """raises if event target name was not found in the map"""
        with pytest.raises(Exception, match="Error on parsing HcsDidEvent: create - data is not supported"):
            _parse_hcs_did_event(str_to_b64('{"data":"data"}'), DidDocumentOperation.CREATE)

    def test_target_not_found(self):
        """raises if event target name was not found in the map"""
        with pytest.raises(Exception, match="Error on parsing HcsDidEvent: create - data is not supported"):
            _parse_hcs_did_event(str_to_b64('{"data":"data"}'), DidDocumentOperation.CREATE)

    def test_data_not_object(self):
        """returns null if data not an object"""
        with pytest.raises(Exception):  # noqa: B017
            _parse_hcs_did_event(str_to_b64("invalid"), DidDocumentOperation.CREATE)

    def test_target_null(self):
        """raises if event target data is null"""
        with pytest.raises(Exception, match="HcsDidUpdateServiceEvent JSON parsing failed: Invalid JSON structure"):
            _parse_hcs_did_event(str_to_b64('{"Service":null}'), DidDocumentOperation.CREATE)

    def test_event_target_data_empty(self):
        """raises if event target data is empty"""
        with pytest.raises(Exception, match="HcsDidUpdateServiceEvent JSON parsing failed: Invalid JSON structure"):
            _parse_hcs_did_event(str_to_b64('{"Service":{}}'), DidDocumentOperation.UPDATE)
