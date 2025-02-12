import pytest

from hiero_did_sdk_python.anoncreds.models.revocation import AnonCredsRevRegEntry, RevRegEntryValue

MOCK_REV_REG_ENTRY_PARAMS = {
    "ver": "mock-version",
    "value": RevRegEntryValue(accum="mock-accum", prev_accum="mock-prev-accum", revoked=[0, 1], issued=[4]),
}

MOCK_REV_REG_ENTRY_JSON_PAYLOAD = {
    "ver": MOCK_REV_REG_ENTRY_PARAMS["ver"],
    "value": MOCK_REV_REG_ENTRY_PARAMS["value"].get_json_payload(),
}

MOCK_COMPRESSED_REV_REG_ENTRY_PAYLOAD = {
    "payload": "KLUv/SB7vQIA8kQRF5CnOjI0FFNxmbsw02bkd0RlDDDS9ccc75HCSCC1qTcSgMDjg2yMnU1dgU1dN6ZmTLnzeDZC2RtfUIdp7oCMSve45t4FBQBmDjbURnwejjkCTKHK"
}


class TestAnonCredsRevRegEntry:
    def test_serializes_to_json(self):
        rev_reg_entry = AnonCredsRevRegEntry(**MOCK_REV_REG_ENTRY_PARAMS)
        assert rev_reg_entry.get_json_payload() == MOCK_COMPRESSED_REV_REG_ENTRY_PAYLOAD

    def test_deserializes_from_json(self):
        AnonCredsRevRegEntry.from_json_payload(MOCK_COMPRESSED_REV_REG_ENTRY_PAYLOAD)

    def test_serializes_to_json_raw(self):
        rev_reg_entry = AnonCredsRevRegEntry(**MOCK_REV_REG_ENTRY_PARAMS)
        assert rev_reg_entry._get_json_payload_raw() == MOCK_REV_REG_ENTRY_JSON_PAYLOAD

    def test_deserializes_from_json_raw(self):
        AnonCredsRevRegEntry._from_json_payload_raw(MOCK_REV_REG_ENTRY_JSON_PAYLOAD)

    def test_throws_on_invalid_json(self):
        with pytest.raises(
            Exception, match=f"{AnonCredsRevRegEntry.__name__} JSON parsing failed: Invalid JSON structure"
        ):
            AnonCredsRevRegEntry.from_json_payload({})
