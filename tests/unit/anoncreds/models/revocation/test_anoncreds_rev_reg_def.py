import pytest

from hiero_did_sdk_python import AnonCredsRevRegDef, RevRegDefValue

MOCK_REV_REG_DEF_PARAMS = {
    "issuer_id": "did:hedera:testnet:zvAQyPeUecGck2EsxcsihxhAB6jZurFrBbj2gC7CNkS5o_0.0.5063027",
    "cred_def_id": "mock-cred-def-tag",
    "tag": "mock-rev-reg-def-tag",
    "value": RevRegDefValue(
        public_keys={"accumKey": {"z": "mock-accum-key"}},
        max_cred_num=10,
        tails_location="mock-tails-location",
        tails_hash="mock-tails-hash",
    ),
}

MOCK_REV_REG_DEF_JSON_PAYLOAD = {
    "issuerId": MOCK_REV_REG_DEF_PARAMS["issuer_id"],
    "type": "CL_ACCUM",
    "credDefId": MOCK_REV_REG_DEF_PARAMS["cred_def_id"],
    "tag": MOCK_REV_REG_DEF_PARAMS["tag"],
    "value": MOCK_REV_REG_DEF_PARAMS["value"].get_json_payload(),
}


class TestAnonCredsRevRegDef:
    def test_serializes_to_json(self):
        rev_reg_def = AnonCredsRevRegDef(**MOCK_REV_REG_DEF_PARAMS)
        assert rev_reg_def.get_json_payload() == MOCK_REV_REG_DEF_JSON_PAYLOAD

    def test_deserializes_from_json(self):
        AnonCredsRevRegDef.from_json_payload(MOCK_REV_REG_DEF_JSON_PAYLOAD)

    def test_throws_on_invalid_json(self):
        with pytest.raises(
            Exception, match=f"{AnonCredsRevRegDef.__name__} JSON parsing failed: Invalid JSON structure"
        ):
            AnonCredsRevRegDef.from_json_payload({})
