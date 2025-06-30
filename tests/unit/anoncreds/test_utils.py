import pytest

from hiero_did_sdk_python.anoncreds.utils import (
    ANONCREDS_IDENTIFIER_SEPARATOR,
    ANONCREDS_OBJECT_FAMILY,
    ANONCREDS_VERSION,
    AnonCredsObjectType,
    build_anoncreds_identifier,
    parse_anoncreds_identifier,
)

PUBLISHER_DID_1 = "did:hedera:testnet:z6MkgUv5CvjRP6AsvEYqSRN7djB6p4zK9bcMQ93g5yK6Td7N_0.0.29613327"
PUBLISHER_DID_2 = "did:hedera:testnet:z6MkgUv5CvjRP6AsvEYqSRN7djB6p4zK9bcMQ93g5yK6Td7N_0.0.29613330"

TOPIC_ID_1 = "0.0.29613330"
TOPIC_ID_2 = "0.0.29613340"


class TestAnonCredsUtils:
    @pytest.mark.parametrize(
        "publisher_did, object_type, topic_id",
        [
            (PUBLISHER_DID_1, AnonCredsObjectType.SCHEMA, TOPIC_ID_1),
            (PUBLISHER_DID_2, AnonCredsObjectType.PUBLIC_CRED_DEF, TOPIC_ID_2),
            (PUBLISHER_DID_1, AnonCredsObjectType.REV_REG, TOPIC_ID_2),
            (PUBLISHER_DID_2, AnonCredsObjectType.REV_REG_ENTRY, TOPIC_ID_2),
        ],
    )
    def test_parse_anoncreds_identifier(self, publisher_did, object_type, topic_id):
        identifier = ANONCREDS_IDENTIFIER_SEPARATOR.join([
            publisher_did,
            ANONCREDS_OBJECT_FAMILY,
            ANONCREDS_VERSION,
            object_type,
            topic_id,
        ])

        parsed_identifier = parse_anoncreds_identifier(identifier)

        assert parsed_identifier.publisher_did == publisher_did
        assert parsed_identifier.object_type == object_type
        assert parsed_identifier.topic_id == topic_id

    @pytest.mark.parametrize(
        "invalid_identifier, expected_error_message",
        [
            ("invalid_identifier", "Identifier has invalid structure"),
            (
                f"{PUBLISHER_DID_1}/non-anoncreds/v1/{AnonCredsObjectType.SCHEMA}/{TOPIC_ID_1}",
                "Identifier contains invalid object definition",
            ),
            (f"{PUBLISHER_DID_1}/anoncreds/v1/INVALID_TYPE/{TOPIC_ID_1}", "Invalid AnonCreds object type"),
            (f"invalid_did/anoncreds/v1/{AnonCredsObjectType.SCHEMA}/{TOPIC_ID_1}", "Cannot parse issuer identifier"),
        ],
    )
    def test_parse_throws_on_invalid_data(self, invalid_identifier, expected_error_message):
        with pytest.raises(Exception, match=expected_error_message):
            parse_anoncreds_identifier(invalid_identifier)

    @pytest.mark.parametrize(
        "publisher_did, object_type, topic_id",
        [
            (PUBLISHER_DID_1, AnonCredsObjectType.SCHEMA, TOPIC_ID_1),
            (PUBLISHER_DID_2, AnonCredsObjectType.PUBLIC_CRED_DEF, TOPIC_ID_2),
            (PUBLISHER_DID_1, AnonCredsObjectType.REV_REG, TOPIC_ID_2),
            (PUBLISHER_DID_2, AnonCredsObjectType.REV_REG_ENTRY, TOPIC_ID_2),
        ],
    )
    def test_build_anoncreds_identifier(self, publisher_did, object_type, topic_id):
        expected_identifier = ANONCREDS_IDENTIFIER_SEPARATOR.join([
            publisher_did,
            ANONCREDS_OBJECT_FAMILY,
            ANONCREDS_VERSION,
            object_type,
            topic_id,
        ])

        identifier = build_anoncreds_identifier(publisher_did, topic_id, object_type)

        assert identifier == expected_identifier
