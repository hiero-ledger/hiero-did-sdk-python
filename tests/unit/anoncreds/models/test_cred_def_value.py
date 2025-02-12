import pytest

from hiero_did_sdk_python import CredDefValue, CredDefValuePrimary, CredDefValueRevocation

MOCK_CRED_DEF_VALUE_PRIMARY_PARAMS = {"n": "n", "s": "s", "r": {"key": "value"}, "rctxt": "rctxt", "z": "z"}
MOCK_CRED_DEF_VALUE_REVOCATION_PARAMS = {
    "g": "g",
    "g_dash": "g_dash",
    "h": "h",
    "h0": "h0",
    "h1": "h1",
    "h2": "h2",
    "htilde": "htilde",
    "h_cap": "h_cap",
    "u": "u",
    "pk": "pk",
    "y": "y",
}

MOCK_CRED_DEF_VALUE_PARAMS = {
    "primary": CredDefValuePrimary(**MOCK_CRED_DEF_VALUE_PRIMARY_PARAMS),
    "revocation": CredDefValueRevocation(**MOCK_CRED_DEF_VALUE_REVOCATION_PARAMS),
}
MOCK_CRED_DEF_VALUE_JSON_PAYLOAD = {
    "primary": MOCK_CRED_DEF_VALUE_PARAMS["primary"].get_json_payload(),
    "revocation": MOCK_CRED_DEF_VALUE_PARAMS["revocation"].get_json_payload(),
}


class TestCredDefValue:
    def test_serializes_to_json(self):
        cred_def_value = CredDefValue(**MOCK_CRED_DEF_VALUE_PARAMS)
        assert cred_def_value.get_json_payload() == MOCK_CRED_DEF_VALUE_JSON_PAYLOAD

    def test_deserializes_from_json(self):
        CredDefValue.from_json_payload(MOCK_CRED_DEF_VALUE_JSON_PAYLOAD)

    def test_deserializes_from_json_without_revocation_part(self):
        payload_without_revocation = {"primary": MOCK_CRED_DEF_VALUE_JSON_PAYLOAD["primary"]}
        CredDefValue.from_json_payload(payload_without_revocation)

    def test_throws_on_invalid_json(self):
        with pytest.raises(Exception, match=f"{CredDefValue.__name__} JSON parsing failed: Invalid JSON structure"):
            CredDefValue.from_json_payload({})

    class TestCredDefValuePrimary:
        def test_serializes_to_json(self):
            cred_def_value_primary = CredDefValuePrimary(**MOCK_CRED_DEF_VALUE_PRIMARY_PARAMS)
            assert cred_def_value_primary.get_json_payload() == MOCK_CRED_DEF_VALUE_PRIMARY_PARAMS

        def test_deserializes_from_json(self):
            CredDefValuePrimary.from_json_payload(MOCK_CRED_DEF_VALUE_PRIMARY_PARAMS)

        def test_throws_on_invalid_json(self):
            with pytest.raises(
                Exception, match=f"{CredDefValuePrimary.__name__} JSON parsing failed: Invalid JSON structure"
            ):
                CredDefValuePrimary.from_json_payload({})

    class TestCredDefValueRevocation:
        def test_serializes_to_json(self):
            cred_def_value_revocation = CredDefValueRevocation(**MOCK_CRED_DEF_VALUE_REVOCATION_PARAMS)
            assert cred_def_value_revocation.get_json_payload() == MOCK_CRED_DEF_VALUE_REVOCATION_PARAMS

        def test_deserializes_from_json(self):
            CredDefValueRevocation.from_json_payload(MOCK_CRED_DEF_VALUE_REVOCATION_PARAMS)

        def test_throws_on_invalid_json(self):
            with pytest.raises(
                Exception, match=f"{CredDefValueRevocation.__name__} JSON parsing failed: Invalid JSON structure"
            ):
                CredDefValueRevocation.from_json_payload({})
