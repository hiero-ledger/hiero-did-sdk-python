import pytest

from hiero_did_sdk_python import AnonCredsSchema

MOCK_SCHEMA_PARAMS = {
    "name": "mock-schema",
    "issuer_id": "did:hedera:testnet:zvAQyPeUecGck2EsxcsihxhAB6jZurFrBbj2gC7CNkS5o_0.0.5063027",
    "attr_names": ["mock-attr-1", "mock-attr-2"],
    "version": "1",
}
MOCK_SCHEMA_JSON_PAYLOAD = {
    "name": MOCK_SCHEMA_PARAMS["name"],
    "issuerId": MOCK_SCHEMA_PARAMS["issuer_id"],
    "attrNames": MOCK_SCHEMA_PARAMS["attr_names"],
    "version": MOCK_SCHEMA_PARAMS["version"],
}


class TestAnonCredsSchema:
    def test_serializes_to_json(self):
        schema = AnonCredsSchema(**MOCK_SCHEMA_PARAMS)
        assert schema.get_json_payload() == MOCK_SCHEMA_JSON_PAYLOAD

    def test_deserializes_from_json(self):
        AnonCredsSchema.from_json_payload(MOCK_SCHEMA_JSON_PAYLOAD)

    def test_throws_on_invalid_json(self):
        with pytest.raises(Exception, match=f"{AnonCredsSchema.__name__} JSON parsing failed: Invalid JSON structure"):
            AnonCredsSchema.from_json_payload({})
