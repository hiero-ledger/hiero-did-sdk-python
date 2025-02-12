import pytest

from hiero_did_sdk_python import AnonCredsCredDef, CredDefValue, CredDefValuePrimary

MOCK_CRED_DEF_PARAMS = {
    "schema_id": "mock_schema_id",
    "issuer_id": "did:hedera:testnet:zvAQyPeUecGck2EsxcsihxhAB6jZurFrBbj2gC7CNkS5o_0.0.5063027",
    "value": CredDefValue(CredDefValuePrimary(n="n", s="s", r={"key": "value"}, rctxt="rctxt", z="z"), None),
    "tag": "mock-tag",
}
MOCK_CRED_DEF_JSON_PAYLOAD = {
    "issuerId": MOCK_CRED_DEF_PARAMS["issuer_id"],
    "schemaId": MOCK_CRED_DEF_PARAMS["schema_id"],
    "type": "CL",
    "tag": MOCK_CRED_DEF_PARAMS["tag"],
    "value": MOCK_CRED_DEF_PARAMS["value"].get_json_payload(),
}


class TestAnonCredsCredDef:
    def test_serializes_to_json(self):
        cred_def = AnonCredsCredDef(**MOCK_CRED_DEF_PARAMS)
        assert cred_def.get_json_payload() == MOCK_CRED_DEF_JSON_PAYLOAD

    def test_deserializes_from_json(self):
        AnonCredsCredDef.from_json_payload(MOCK_CRED_DEF_JSON_PAYLOAD)

    def test_throws_on_invalid_json(self):
        with pytest.raises(Exception, match=f"{AnonCredsCredDef.__name__} JSON parsing failed: Invalid JSON structure"):
            AnonCredsCredDef.from_json_payload({})
