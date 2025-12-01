import asyncio

import pytest
from hiero_sdk_python import Client

from hiero_did_sdk_python import HederaDid, HederaDidResolver
from hiero_did_sdk_python.utils.encoding import bytes_to_b58

from .conftest import OPERATOR_KEY, OPERATOR_KEY_DER, OPERATOR_KEY_TYPE


# @pytest.mark.flaky(retries=3, delay=1)
@pytest.mark.asyncio(loop_scope="session")
class TestHederaDidResolver:
    async def test_returns_error_response(self, client: Client):
        """Returns error response"""
        resolver = HederaDidResolver(client)

        result = await resolver.resolve("did:hedera:testnet:nNCTE5bZdRmjm2obqJwS892jVLak_0.0.1")
        assert result == {
            "didDocument": None,
            "didDocumentMetadata": {},
            "didResolutionMetadata": {
                "error": "invalidDid",
                "message": "DID string is invalid. ID holds incorrect format.",
            },
        }

        result = await resolver.resolve("")
        assert result == {
            "didDocument": None,
            "didDocumentMetadata": {},
            "didResolutionMetadata": {
                "error": "invalidDid",
                "message": "DID string is invalid: topic ID is missing",
            },
        }

        result = await resolver.resolve(
            "did:hedera:invalidNetwork:nNCTE5bZdRmjm2obqJwS892jVLakafasdfasdfasffwvdasdfasqqwe_0.0.1"
        )
        assert result == {
            "didDocument": None,
            "didDocumentMetadata": {},
            "didResolutionMetadata": {
                "error": "unknownNetwork",
                "message": "DID string is invalid. Invalid Hedera network.",
            },
        }

    async def test_returns_success_response(self, client: Client, Something):
        """Returns success response"""
        did = HederaDid(client=client, private_key_der=OPERATOR_KEY_DER)

        await did.register()
        await did.add_or_update_service(
            id_=f"{did.identifier}#service-1", service_type="LinkedDomains", service_endpoint="https://example.com/vcs"
        )

        assert did.identifier

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(5)

        result = await HederaDidResolver(client).resolve(did.identifier)

        assert result == {
            "didDocument": {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key"],
                "authentication": [f"{did.identifier}#did-root-key"],
                "id": did.identifier,
                "service": [
                    {
                        "id": f"{did.identifier}#service-1",
                        "serviceEndpoint": "https://example.com/vcs",
                        "type": "LinkedDomains",
                    },
                ],
                "verificationMethod": [
                    {
                        "controller": did.identifier,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(OPERATOR_KEY.public_key().to_bytes_raw())),
                        "type": OPERATOR_KEY_TYPE,
                    },
                ],
            },
            "didDocumentMetadata": {
                "created": Something,
                "updated": Something,
                "deactivated": False,
            },
            "didResolutionMetadata": {
                "contentType": "application/did+ld+json",
            },
        }

    async def test_returns_deactivated_document(self, client: Client):
        """Returns deactivated DID document"""
        did = HederaDid(client=client, private_key_der=OPERATOR_KEY_DER)

        await did.register()
        await did.delete()

        assert did.identifier

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(5)

        result = await HederaDidResolver(client).resolve(did.identifier)

        assert result == {
            "didDocument": {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [],
                "authentication": [],
                "id": did.identifier,
                "verificationMethod": [],
            },
            "didDocumentMetadata": {
                "deactivated": True,
            },
            "didResolutionMetadata": {
                "contentType": "application/did+ld+json",
            },
        }
