import pytest

from hiero_did_sdk_python import RevRegDefValue

MOCK_REV_REG_DEF_VALUE_PARAMS = {
    "public_keys": {"accumKey": {"z": "mock-accum-key"}},
    "max_cred_num": 10,
    "tails_location": "mock-tails-location",
    "tails_hash": "mock-tails-hash",
}

MOCK_REV_REG_DEF_VALUE_JSON_PAYLOAD = {
    "publicKeys": MOCK_REV_REG_DEF_VALUE_PARAMS["public_keys"],
    "maxCredNum": MOCK_REV_REG_DEF_VALUE_PARAMS["max_cred_num"],
    "tailsLocation": MOCK_REV_REG_DEF_VALUE_PARAMS["tails_location"],
    "tailsHash": MOCK_REV_REG_DEF_VALUE_PARAMS["tails_hash"],
}


class TestRevRegDefValue:
    def test_serializes_to_json(self):
        rev_reg_def = RevRegDefValue(**MOCK_REV_REG_DEF_VALUE_PARAMS)
        assert rev_reg_def.get_json_payload() == MOCK_REV_REG_DEF_VALUE_JSON_PAYLOAD

    def test_deserializes_from_json(self):
        RevRegDefValue.from_json_payload(MOCK_REV_REG_DEF_VALUE_JSON_PAYLOAD)

    def test_throws_on_invalid_json(self):
        with pytest.raises(Exception, match=f"{RevRegDefValue.__name__} JSON parsing failed: Invalid JSON structure"):
            RevRegDefValue.from_json_payload({})
