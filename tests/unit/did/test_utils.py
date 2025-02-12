import pytest

from hiero_did_sdk_python.did.did_error import DidException
from hiero_did_sdk_python.did.utils import ParsedIdentifier, build_identifier, parse_identifier
from hiero_did_sdk_python.utils.encoding import multibase_encode

from .common import PRIVATE_KEY


class TestUtils:
    @pytest.mark.parametrize(
        ("identifier", "expected_exception", "expected_message"),
        (
            ("", DidException, "DID string is invalid: topic ID is missing"),
            ("invalidDid1", DidException, "DID string is invalid: topic ID is missing"),
            ("did:invalid", DidException, "DID string is invalid: topic ID is missing"),
            (
                "did:invalidMethod:8LjUL78kFVnWV9rFnNCTE5bZdRmjm2obqJwS892jVLak_0.0.24352",
                DidException,
                "DID string is invalid: invalid method name: invalidMethod",
            ),
            (
                "did:hedera:invalidNetwork:8LjUL78kFVnWV9rFnNCTE5bZdRmjm2obqJwS892jVLak_0.0.24352",
                DidException,
                "DID string is invalid. Invalid Hedera network.",
            ),
            (
                "did:hedera:invalidNetwork:8LjUL78kFVnWV9rFnNCTE5bZdRmjm2obqJwS892jVLak_",
                DidException,
                "DID string is invalid. topic ID is missing",
            ),
            (
                "did:hedera:testnet:invalidAddress_0.0.24352_1.5.23462345",
                ValueError,
                "too many values to unpack \\(expected 2\\)",
            ),
            ("did:hedera:testnet_1.5.23462345", DidException, "DID string is invalid. pop from empty list"),
            (
                "did:hedera:testnet:z6Mk8LjUL78kFVnWV9rFnNCTE5bZdRmjm2obqJwS892jVLak:unknown:parameter=1_missing",
                DidException,
                "DID string is invalid. ID holds incorrect format.",
            ),
            (
                "did:hedera:testnet:z6Mk8LjUL78kFVnWV9rFnNCTE5bZdRmjm2obqJwS892jVLak_0.0.1=1",
                DidException,
                "DID string is invalid. Topic ID doesn't match pattern",
            ),
            (
                "did:hedera:testnet:z6Mk8LjUL78kFVnWV9rFnNCTE5bZdRmjm2obqJwS892jVLak:hedera:testnet:fid",
                DidException,
                "DID string is invalid: topic ID is missing",
            ),
            (
                "did:hedera:testnet:z6Mk8LjUL78kFVnWV9rFnNCTE5bZdRmjm2obqJwS892jVLak:unknownPart_0.0.1",
                DidException,
                "DID string is invalid. ID holds incorrect format.",
            ),
            (
                "did:notHedera:testnet:z6Mk8LjUL78kFVnWV9rFnNCTE5bZdRmjm2obqJwS892jVLak_0.0.1",
                DidException,
                "DID string is invalid. invalid method name: notHedera",
            ),
        ),
    )
    def test_parse_invalid_identifier_throws_error(self, identifier, expected_exception, expected_message):
        """throw an error when invalid did string provided"""
        with pytest.raises(expected_exception, match=expected_message):
            parse_identifier(identifier)

    @pytest.mark.parametrize(
        ("network", "subnetwork", "encoded_string", "topic_id"),
        (
            ("hedera", "testnet", "z87meAWt7t2zrDxo7qw3PVTjexKWReYWS75LH29THy8kb", "0.0.29643290"),
            (
                "hedera",
                "testnet",
                "2JjAddF8hvcU9gFQJrx7uZFAcSzXbu4YvadiFoJk6aKw3LPwDnE9UsoQjS8sEJgi5xyzNHk5PF2Gh",
                "0.0.5047476",
            ),
        ),
    )
    def test_parse_valid_identifier(self, network, subnetwork, encoded_string, topic_id):
        """should part from pre-defined string and provide HcsDid object"""
        identifier = f"did:{network}:{subnetwork}:{encoded_string}_{topic_id}"

        parsed_identifier = parse_identifier(identifier)

        assert isinstance(parsed_identifier, ParsedIdentifier)
        assert parsed_identifier.network == subnetwork
        assert parsed_identifier.topic_id == topic_id
        assert parsed_identifier.public_key_base58 == encoded_string

    def test_parse_valid_identifier_from_private_key(self):
        """should parse from string and provide HcsDid object"""
        public_key_bytes = bytes(PRIVATE_KEY.public_key().to_bytes_raw())
        base58_btc_encoded_string = multibase_encode(public_key_bytes, "base58btc")

        identifier = f"did:hedera:testnet:{base58_btc_encoded_string}_0.0.1"

        assert isinstance(parse_identifier(identifier), ParsedIdentifier)

    @pytest.mark.parametrize(
        ("subnetwork", "public_key", "topic_id"),
        (
            ("testnet", "z6Mk8LjUL78kFVnWV9rFnNCTE5bZdRmjm2obqJwS892jVLak", "0.0.1"),
            ("mainnet", "7Prd74ry1Uct87nZqL3ny7aR7Cg46JamVbJgk8azVgUm", "0.0.12345"),
        ),
    )
    def test_build_identifier(self, subnetwork, public_key, topic_id):
        identifier = build_identifier(subnetwork, public_key, topic_id)

        assert isinstance(identifier, str)
        assert identifier == f"did:hedera:{subnetwork}:{public_key}_{topic_id}"
