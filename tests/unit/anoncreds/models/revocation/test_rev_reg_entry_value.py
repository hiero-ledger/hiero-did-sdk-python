import pytest

from hiero_did_sdk_python.anoncreds.models.revocation import RevRegEntryValue

MOCK_REV_REG_ENTRY_VALUE_PARAMS = {
    "accum": "mock-accum",
    "prev_accum": "mock-prev-accum",
    "revoked": [0, 1],
    "issued": [4],
}

MOCK_REV_REG_ENTRY_VALUE_JSON_PAYLOAD = {
    "accum": MOCK_REV_REG_ENTRY_VALUE_PARAMS["accum"],
    "prevAccum": MOCK_REV_REG_ENTRY_VALUE_PARAMS["prev_accum"],
    "revoked": MOCK_REV_REG_ENTRY_VALUE_PARAMS["revoked"],
    "issued": MOCK_REV_REG_ENTRY_VALUE_PARAMS["issued"],
}


class TestRevRegEntryValue:
    def test_serializes_to_json(self):
        rev_reg_entry_value = RevRegEntryValue(**MOCK_REV_REG_ENTRY_VALUE_PARAMS)
        assert rev_reg_entry_value.get_json_payload() == MOCK_REV_REG_ENTRY_VALUE_JSON_PAYLOAD

    def test_deserializes_from_json(self):
        RevRegEntryValue.from_json_payload(MOCK_REV_REG_ENTRY_VALUE_JSON_PAYLOAD)

    def test_throws_on_invalid_json(self):
        with pytest.raises(Exception, match=f"{RevRegEntryValue.__name__} JSON parsing failed: Invalid JSON structure"):
            RevRegEntryValue.from_json_payload({})
