import asyncio
import re
from typing import cast

import pytest
from hiero_sdk_python import Client, PrivateKey, PublicKey

from hiero_did_sdk_python import DidException, HederaDid
from hiero_did_sdk_python.did.hcs import HcsDidMessageEnvelope
from hiero_did_sdk_python.did.types import SupportedKeyType
from hiero_did_sdk_python.hcs import HcsMessageResolver
from hiero_did_sdk_python.utils.encoding import b58_to_bytes, bytes_to_b58, multibase_encode
from hiero_did_sdk_python.utils.keys import get_key_type

from .conftest import NETWORK, OPERATOR_KEY, OPERATOR_KEY_DER, OPERATOR_KEY_TYPE

TOPIC_REGEX = re.compile(r"^0\.0\.[0-9]{3,}")

VALID_DID = f"did:hedera:{NETWORK}:z6MkgUv5CvjRP6AsvEYqSRN7djB6p4zK9bcMQ93g5yK6Td7N_0.0.29613327"

VERIFICATION_PUBLIC_KEY_BASE58 = "87meAWt7t2zrDxo7qw3PVTjexKWReYWS75LH29THy8kb"
VERIFICATION_PUBLIC_KEY = PublicKey.from_bytes(b58_to_bytes(VERIFICATION_PUBLIC_KEY_BASE58))
VERIFICATION_PUBLIC_KEY_DER = VERIFICATION_PUBLIC_KEY.to_string_raw()
VERIFICATION_PUBLIC_KEY_TYPE: SupportedKeyType = "Ed25519VerificationKey2018"
VERIFICATION_ID = f"did:hedera:{NETWORK}:z{VERIFICATION_PUBLIC_KEY_BASE58}_0.0.29617801#key-1"


async def create_and_register_new_did(client: Client, private_key_der=OPERATOR_KEY_DER):
    did = HederaDid(client=client, private_key_der=private_key_der)
    await did.register()
    return did


async def resolve_did_topic_messages(topic_id: str, client: Client):
    return await HcsMessageResolver(topic_id, HcsDidMessageEnvelope).execute(client)


# @pytest.mark.flaky(retries=3, delay=1)
@pytest.mark.asyncio(loop_scope="session")
class TestHederaDid:
    class TestRegister:
        async def test_throws_if_already_registered(self, client: Client):
            """Throws error if DID is already registered"""
            did = await create_and_register_new_did(client)

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            with pytest.raises(DidException, match="DID is already registered"):
                await did.register()

        async def test_throws_on_missing_private_key(self, client: Client):
            """Throws error if private key is not provided"""
            did = HederaDid(client=client, identifier=VALID_DID)

            with pytest.raises(DidException, match="Private key is required to register new DID"):
                await did.register()

        async def test_creates_new_did(self, client: Client):
            """Creates a new DID by registering HCS topic and submitting a first topic message"""
            did = await create_and_register_new_did(client)
            assert did.topic_id

            expected_identifier = f"did:hedera:{NETWORK}:{multibase_encode(bytes(OPERATOR_KEY.public_key().to_bytes_raw()), "base58btc")}_{did.topic_id}"

            assert bool(TOPIC_REGEX.match(did.topic_id))
            assert did.identifier == expected_identifier
            assert cast(PrivateKey, did._private_key).to_string() == OPERATOR_KEY.to_string()
            assert did.network == NETWORK

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 1

        async def test_recreates_deleted_did_with_same_topic(self, client: Client):
            """Re-creates deleted DID without creating a new topic"""
            did = await create_and_register_new_did(client)
            assert did.topic_id

            original_topic_id = did.topic_id

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 1

            await did.delete()
            assert did.topic_id == original_topic_id

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 2

            await did.register()
            assert did.topic_id == original_topic_id

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 3

    class TestResolve:
        async def test_throws_if_not_registered(self, client: Client):
            """Throws error if DID is not registered"""
            did = HederaDid(client=client, private_key_der=OPERATOR_KEY_DER)

            with pytest.raises(DidException, match="DID is not registered"):
                await did.resolve()

        async def test_successfully_resolves_registered(self, client: Client):
            """Successfully resolves just registered DID"""
            did = await create_and_register_new_did(client)

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key"],
                "authentication": [f"{did.identifier}#did-root-key"],
                "id": did.identifier,
                "verificationMethod": [
                    {
                        "controller": did.identifier,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(OPERATOR_KEY.public_key().to_bytes_raw())),
                        "type": OPERATOR_KEY_TYPE,
                    },
                ],
            }

    class TestDelete:
        async def test_throws_error_if_not_registered(self, client: Client):
            """Throws error if DID is not registered"""
            did = HederaDid(client=client, private_key_der=OPERATOR_KEY_DER)

            with pytest.raises(DidException, match="DID is not registered"):
                await did.delete()

        async def test_throws_on_missing_private_key(self, client: Client):
            """Throws error if private key is not provided"""
            did = HederaDid(client=client, identifier=VALID_DID)

            with pytest.raises(DidException, match="Private key is required to submit DID event transaction"):
                await did.delete()

        async def test_deletes_did_document(self, client: Client):
            """Deletes DID document"""
            did = await create_and_register_new_did(client)
            assert did.topic_id

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(10)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key"],
                "authentication": [f"{did.identifier}#did-root-key"],
                "id": did.identifier,
                "verificationMethod": [
                    {
                        "controller": did.identifier,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(OPERATOR_KEY.public_key().to_bytes_raw())),
                        "type": OPERATOR_KEY_TYPE,
                    },
                ],
            }

            await did.delete()

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [],
                "authentication": [],
                "id": did.identifier,
                "verificationMethod": [],
            }

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 2

    class TestChangeOwner:
        NEW_OWNER_ID = f"did:hedera:{NETWORK}:z6MkgUv5CvjRP6AsvEYqSRN7djB6p4zK9bcMQ93g5yK6Td7N_0.0.99999999"

        async def test_throws_error_if_not_registered(self, client: Client):
            """Throws error if DID is not registered"""
            did = HederaDid(client=client, private_key_der=OPERATOR_KEY_DER)

            with pytest.raises(DidException, match="DID is not registered"):
                await did.change_owner(
                    controller=self.NEW_OWNER_ID, new_private_key_der=PrivateKey.generate_ed25519().to_string()
                )

        async def test_throws_on_missing_private_key(self, client: Client):
            """Throws error if private key is not provided"""
            did = HederaDid(client=client, identifier=VALID_DID)

            new_private_key = PrivateKey.generate_ed25519()
            with pytest.raises(DidException, match="Private key is required to submit DID event transaction"):
                await did.change_owner(controller=self.NEW_OWNER_ID, new_private_key_der=new_private_key.to_string())

        async def test_changes_document_owner(self, client: Client):
            """Changes the owner of the document"""
            did = await create_and_register_new_did(client)
            assert did.topic_id

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            new_private_key = PrivateKey.generate_ed25519()
            new_private_key_type = get_key_type(new_private_key)
            await did.change_owner(controller=self.NEW_OWNER_ID, new_private_key_der=new_private_key.to_string())

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key"],
                "authentication": [f"{did.identifier}#did-root-key"],
                "controller": self.NEW_OWNER_ID,
                "id": did.identifier,
                "verificationMethod": [
                    {
                        "controller": self.NEW_OWNER_ID,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(new_private_key.public_key().to_bytes_raw())),
                        "type": new_private_key_type,
                    },
                ],
            }

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 2

    class TestService:
        async def test_throws_error_if_not_registered(self, client: Client):
            """Throws error if DID is not registered"""
            did = HederaDid(client=client, private_key_der=OPERATOR_KEY_DER)

            with pytest.raises(DidException, match="DID is not registered"):
                await did.add_or_update_service(
                    id_=f"{did.identifier}#service-1",
                    service_type="LinkedDomains",
                    service_endpoint="https://example.com/vcs",
                )

            with pytest.raises(DidException, match="DID is not registered"):
                await did.add_or_update_service(
                    id_=f"{did.identifier}#service-1",
                    service_type="LinkedDomains",
                    service_endpoint="https://example.com/vcs",
                )

            with pytest.raises(DidException, match="DID is not registered"):
                await did.revoke_service(id_=f"{did.identifier}#service-1")

        async def test_throws_on_missing_private_key(self, client: Client):
            """Throws error if private key is not provided"""
            did = HederaDid(client=client, identifier=VALID_DID)

            with pytest.raises(DidException, match="Private key is required to submit DID event transaction"):
                await did.add_or_update_service(
                    id_=f"{did.identifier}#service-1",
                    service_type="LinkedDomains",
                    service_endpoint="https://example.com/vcs",
                )

            with pytest.raises(DidException, match="Private key is required to submit DID event transaction"):
                await did.add_or_update_service(
                    id_=f"{did.identifier}#service-1",
                    service_type="LinkedDomains",
                    service_endpoint="https://example.com/vcs",
                )

            with pytest.raises(DidException, match="Private key is required to submit DID event transaction"):
                await did.revoke_service(id_=f"{did.identifier}#service-1")

        async def test_throws_on_invalid_event_id(self, client: Client):
            """Throws error if event id is not valid"""
            did = HederaDid(client=client, identifier=VALID_DID, private_key_der=OPERATOR_KEY_DER)

            with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#service-{number}"):
                await did.add_or_update_service(
                    id_=f"{did.identifier}#invalid-1", service_type="LinkedDomains", service_endpoint="service-endpoint"
                )

            with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#service-{number}"):
                await did.add_or_update_service(
                    id_=f"{did.identifier}#invalid-1", service_type="LinkedDomains", service_endpoint="service-endpoint"
                )

            with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#service-{number}"):
                await did.revoke_service(id_=f"{did.identifier}#invalid-1")

        async def test_adds_new_service(self, client: Client):
            """Adds new DID service"""
            did = await create_and_register_new_did(client)
            assert did.topic_id

            await did.add_or_update_service(
                id_=f"{did.identifier}#service-1",
                service_type="LinkedDomains",
                service_endpoint="https://example.com/vcs",
            )

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key"],
                "authentication": [f"{did.identifier}#did-root-key"],
                "id": did.identifier,
                "verificationMethod": [
                    {
                        "controller": did.identifier,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(OPERATOR_KEY.public_key().to_bytes_raw())),
                        "type": OPERATOR_KEY_TYPE,
                    },
                ],
                "service": [
                    {
                        "id": f"{did.identifier}#service-1",
                        "serviceEndpoint": "https://example.com/vcs",
                        "type": "LinkedDomains",
                    },
                ],
            }

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 2

        async def test_updates_existing_service(self, client: Client):
            """Updates existing DID service"""
            did = await create_and_register_new_did(client)
            assert did.topic_id

            await did.add_or_update_service(
                id_=f"{did.identifier}#service-1",
                service_type="LinkedDomains",
                service_endpoint="https://example.com/vcs",
            )
            await did.add_or_update_service(
                id_=f"{did.identifier}#service-1",
                service_type="LinkedDomains",
                service_endpoint="https://example.com/updated",
            )

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key"],
                "authentication": [f"{did.identifier}#did-root-key"],
                "id": did.identifier,
                "verificationMethod": [
                    {
                        "controller": did.identifier,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(OPERATOR_KEY.public_key().to_bytes_raw())),
                        "type": OPERATOR_KEY_TYPE,
                    },
                ],
                "service": [
                    {
                        "id": f"{did.identifier}#service-1",
                        "serviceEndpoint": "https://example.com/updated",
                        "type": "LinkedDomains",
                    },
                ],
            }

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 3

        async def test_revokes_existing_service(self, client: Client):
            """Revokes existing DID service"""
            did = await create_and_register_new_did(client)
            assert did.topic_id

            await did.add_or_update_service(
                id_=f"{did.identifier}#service-1",
                service_type="LinkedDomains",
                service_endpoint="https://example.com/vcs",
            )
            await did.revoke_service(id_=f"{did.identifier}#service-1")

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key"],
                "authentication": [f"{did.identifier}#did-root-key"],
                "id": did.identifier,
                "verificationMethod": [
                    {
                        "controller": did.identifier,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(OPERATOR_KEY.public_key().to_bytes_raw())),
                        "type": OPERATOR_KEY_TYPE,
                    },
                ],
            }

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 3

        async def test_recreates_service(self, client: Client):
            """Re-creates revoked DID service"""
            did = await create_and_register_new_did(client)
            assert did.topic_id

            await did.add_or_update_service(
                id_=f"{did.identifier}#service-1",
                service_type="LinkedDomains",
                service_endpoint="https://example.com/vcs",
            )
            await did.revoke_service(
                id_=f"{did.identifier}#service-1",
            )
            await did.add_or_update_service(
                id_=f"{did.identifier}#service-1",
                service_type="LinkedDomains",
                service_endpoint="https://example.com/re-created",
            )

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key"],
                "authentication": [f"{did.identifier}#did-root-key"],
                "id": did.identifier,
                "verificationMethod": [
                    {
                        "controller": did.identifier,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(OPERATOR_KEY.public_key().to_bytes_raw())),
                        "type": OPERATOR_KEY_TYPE,
                    },
                ],
                "service": [
                    {
                        "id": f"{did.identifier}#service-1",
                        "serviceEndpoint": "https://example.com/re-created",
                        "type": "LinkedDomains",
                    },
                ],
            }

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 4

    class TestVerificationMethod:
        async def test_throws_error_if_not_registered(self, client: Client):
            """Throws error if DID is not registered"""
            did = HederaDid(client=client, private_key_der=OPERATOR_KEY_DER)

            with pytest.raises(DidException, match="DID is not registered"):
                await did.add_or_update_verification_method(
                    id_=VERIFICATION_ID,
                    controller=VALID_DID,
                    public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                    type_=VERIFICATION_PUBLIC_KEY_TYPE,
                )

            with pytest.raises(DidException, match="DID is not registered"):
                await did.add_or_update_verification_method(
                    id_=VERIFICATION_ID,
                    controller=VALID_DID,
                    public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                    type_=VERIFICATION_PUBLIC_KEY_TYPE,
                )

            with pytest.raises(DidException, match="DID is not registered"):
                await did.revoke_verification_method(id_=VERIFICATION_ID)

        async def test_throws_on_missing_private_key(self, client: Client):
            """Throws error if private key is not provided"""
            did = HederaDid(client=client, identifier=VALID_DID)

            with pytest.raises(DidException, match="Private key is required to submit DID event transaction"):
                await did.add_or_update_verification_method(
                    id_=VERIFICATION_ID,
                    controller=VALID_DID,
                    public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                    type_=VERIFICATION_PUBLIC_KEY_TYPE,
                )

            with pytest.raises(DidException, match="Private key is required to submit DID event transaction"):
                await did.add_or_update_verification_method(
                    id_=VERIFICATION_ID,
                    controller=VALID_DID,
                    public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                    type_=VERIFICATION_PUBLIC_KEY_TYPE,
                )

            with pytest.raises(DidException, match="Private key is required to submit DID event transaction"):
                await did.revoke_verification_method(id_=VERIFICATION_ID)

        async def test_throws_on_invalid_event_id(self, client: Client):
            """Throws error if event id is not valid"""
            did = HederaDid(client=client, identifier=VALID_DID, private_key_der=OPERATOR_KEY_DER)

            with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#key-{number}"):
                await did.add_or_update_verification_method(
                    id_=f"{did.identifier}#invalid-1",
                    controller=VALID_DID,
                    public_key_der=OPERATOR_KEY.public_key().to_string(),
                    type_=OPERATOR_KEY_TYPE,
                )

            with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#key-{number}"):
                await did.add_or_update_verification_method(
                    id_=f"{did.identifier}#invalid-1",
                    controller=VALID_DID,
                    public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                    type_=VERIFICATION_PUBLIC_KEY_TYPE,
                )

            with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#key-{number}"):
                await did.revoke_verification_method(id_=f"{did.identifier}#invalid-1")

        async def test_adds_new_verification_method(self, client: Client):
            """Adds new DID verification method"""
            did = await create_and_register_new_did(client)
            assert did.topic_id
            assert did.identifier

            await did.add_or_update_verification_method(
                id_=VERIFICATION_ID,
                controller=did.identifier,
                public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                type_=VERIFICATION_PUBLIC_KEY_TYPE,
            )

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(10)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key"],
                "authentication": [f"{did.identifier}#did-root-key"],
                "id": did.identifier,
                "verificationMethod": [
                    {
                        "controller": did.identifier,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(OPERATOR_KEY.public_key().to_bytes_raw())),
                        "type": OPERATOR_KEY_TYPE,
                    },
                    {
                        "controller": did.identifier,
                        "id": VERIFICATION_ID,
                        "publicKeyBase58": VERIFICATION_PUBLIC_KEY_BASE58,
                        "type": VERIFICATION_PUBLIC_KEY_TYPE,
                    },
                ],
            }

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 2

        async def test_updates_existing_verification_method(self, client: Client):
            """Updates existing DID verification method"""
            did = await create_and_register_new_did(client)
            assert did.topic_id
            assert did.identifier

            updated_public_key_base58 = "AvU2AEh8ybRqNwHAM3CjbkjYaYHpt9oA1uugW9EVTg6P"
            updated_public_key = PublicKey.from_bytes(b58_to_bytes(updated_public_key_base58))
            updated_public_key_type = get_key_type(updated_public_key)

            await did.add_or_update_verification_method(
                id_=VERIFICATION_ID,
                controller=did.identifier,
                public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                type_=VERIFICATION_PUBLIC_KEY_TYPE,
            )
            await did.add_or_update_verification_method(
                id_=VERIFICATION_ID,
                controller=did.identifier,
                public_key_der=updated_public_key.to_string(),
                type_=updated_public_key_type,
            )

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key"],
                "authentication": [f"{did.identifier}#did-root-key"],
                "id": did.identifier,
                "verificationMethod": [
                    {
                        "controller": did.identifier,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(OPERATOR_KEY.public_key().to_bytes_raw())),
                        "type": OPERATOR_KEY_TYPE,
                    },
                    {
                        "controller": did.identifier,
                        "id": VERIFICATION_ID,
                        "publicKeyBase58": updated_public_key_base58,
                        "type": updated_public_key_type,
                    },
                ],
            }

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 3

        async def test_revokes_existing_verification_method(self, client: Client):
            """Revokes existing DID verification method"""
            did = await create_and_register_new_did(client)
            assert did.topic_id
            assert did.identifier

            await did.add_or_update_verification_method(
                id_=VERIFICATION_ID,
                controller=did.identifier,
                public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                type_=VERIFICATION_PUBLIC_KEY_TYPE,
            )
            await did.revoke_verification_method(id_=VERIFICATION_ID)

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key"],
                "authentication": [f"{did.identifier}#did-root-key"],
                "id": did.identifier,
                "verificationMethod": [
                    {
                        "controller": did.identifier,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(OPERATOR_KEY.public_key().to_bytes_raw())),
                        "type": OPERATOR_KEY_TYPE,
                    },
                ],
            }

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 3

    class TestVerificationRelationship:
        async def test_throws_error_if_not_registered(self, client: Client):
            """Throws error if DID is not registered"""
            did = HederaDid(client=client, private_key_der=OPERATOR_KEY_DER)

            with pytest.raises(DidException, match="DID is not registered"):
                await did.add_or_update_verification_relationship(
                    id_=VERIFICATION_ID,
                    relationship_type="assertionMethod",
                    controller=VALID_DID,
                    public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                    type_=VERIFICATION_PUBLIC_KEY_TYPE,
                )

            with pytest.raises(DidException, match="DID is not registered"):
                await did.add_or_update_verification_relationship(
                    id_=VERIFICATION_ID,
                    relationship_type="assertionMethod",
                    controller=VALID_DID,
                    public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                    type_=VERIFICATION_PUBLIC_KEY_TYPE,
                )

            with pytest.raises(DidException, match="DID is not registered"):
                await did.revoke_verification_relationship(id_=VERIFICATION_ID, relationship_type="assertionMethod")

        async def test_throws_on_missing_private_key(self, client: Client):
            """Throws error if private key is not provided"""
            did = HederaDid(client=client, identifier=VALID_DID)

            with pytest.raises(DidException, match="Private key is required to submit DID event transaction"):
                await did.add_or_update_verification_relationship(
                    id_=VERIFICATION_ID,
                    relationship_type="assertionMethod",
                    controller=VALID_DID,
                    public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                    type_=VERIFICATION_PUBLIC_KEY_TYPE,
                )

            with pytest.raises(DidException, match="Private key is required to submit DID event transaction"):
                await did.add_or_update_verification_relationship(
                    id_=VERIFICATION_ID,
                    relationship_type="assertionMethod",
                    controller=VALID_DID,
                    public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                    type_=VERIFICATION_PUBLIC_KEY_TYPE,
                )

            with pytest.raises(DidException, match="Private key is required to submit DID event transaction"):
                await did.revoke_verification_relationship(id_=VERIFICATION_ID, relationship_type="assertionMethod")

        async def test_throws_on_invalid_event_id(self, client: Client):
            """Throws error if event id is not valid"""
            did = HederaDid(client=client, identifier=VALID_DID, private_key_der=OPERATOR_KEY_DER)

            with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#key-{number}"):
                await did.add_or_update_verification_relationship(
                    id_=f"{did.identifier}#invalid-1",
                    relationship_type="assertionMethod",
                    controller=VALID_DID,
                    public_key_der=OPERATOR_KEY.public_key().to_string(),
                    type_=OPERATOR_KEY_TYPE,
                )

            with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#key-{number}"):
                await did.add_or_update_verification_relationship(
                    id_=f"{did.identifier}#invalid-1",
                    relationship_type="assertionMethod",
                    controller=VALID_DID,
                    public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                    type_=VERIFICATION_PUBLIC_KEY_TYPE,
                )

            with pytest.raises(Exception, match="Event ID is invalid. Expected format: {did}#key-{number}"):
                await did.revoke_verification_relationship(
                    id_=f"{did.identifier}#invalid-1", relationship_type="assertionMethod"
                )

        async def test_adds_new_verification_relationship(self, client: Client):
            """Adds new DID verification relationship"""
            did = await create_and_register_new_did(client)
            assert did.topic_id
            assert did.identifier

            await did.add_or_update_verification_relationship(
                id_=VERIFICATION_ID,
                relationship_type="authentication",
                controller=did.identifier,
                public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                type_=VERIFICATION_PUBLIC_KEY_TYPE,
            )

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key"],
                "authentication": [f"{did.identifier}#did-root-key", VERIFICATION_ID],
                "id": did.identifier,
                "verificationMethod": [
                    {
                        "controller": did.identifier,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(OPERATOR_KEY.public_key().to_bytes_raw())),
                        "type": OPERATOR_KEY_TYPE,
                    },
                    {
                        "controller": did.identifier,
                        "id": VERIFICATION_ID,
                        "publicKeyBase58": VERIFICATION_PUBLIC_KEY_BASE58,
                        "type": VERIFICATION_PUBLIC_KEY_TYPE,
                    },
                ],
            }

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 2

        async def test_updates_existing_verification_relationship(self, client: Client):
            """Updates existing DID verification relationship"""
            did = await create_and_register_new_did(client)
            assert did.topic_id
            assert did.identifier

            updated_public_key_base58 = "AvU2AEh8ybRqNwHAM3CjbkjYaYHpt9oA1uugW9EVTg6P"
            updated_public_key = PublicKey.from_bytes(b58_to_bytes(updated_public_key_base58))
            updated_public_key_type = get_key_type(updated_public_key)

            await did.add_or_update_verification_relationship(
                id_=VERIFICATION_ID,
                relationship_type="assertionMethod",
                controller=did.identifier,
                public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                type_=VERIFICATION_PUBLIC_KEY_TYPE,
            )
            await did.add_or_update_verification_relationship(
                id_=VERIFICATION_ID,
                relationship_type="assertionMethod",
                controller=did.identifier,
                public_key_der=updated_public_key.to_string(),
                type_=updated_public_key_type,
            )

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key", VERIFICATION_ID],
                "authentication": [f"{did.identifier}#did-root-key"],
                "id": did.identifier,
                "verificationMethod": [
                    {
                        "controller": did.identifier,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(OPERATOR_KEY.public_key().to_bytes_raw())),
                        "type": OPERATOR_KEY_TYPE,
                    },
                    {
                        "controller": did.identifier,
                        "id": VERIFICATION_ID,
                        "publicKeyBase58": updated_public_key_base58,
                        "type": updated_public_key_type,
                    },
                ],
            }

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 3

        async def test_revokes_existing_verification_relationship(self, client: Client):
            """Revokes existing DID verification relationship"""
            did = await create_and_register_new_did(client)
            assert did.topic_id
            assert did.identifier

            await did.add_or_update_verification_relationship(
                id_=VERIFICATION_ID,
                relationship_type="keyAgreement",
                controller=did.identifier,
                public_key_der=VERIFICATION_PUBLIC_KEY_DER,
                type_=VERIFICATION_PUBLIC_KEY_TYPE,
            )
            await did.revoke_verification_relationship(id_=VERIFICATION_ID, relationship_type="keyAgreement")

            # Wait until changes are propagated to Hedera Mirror node
            await asyncio.sleep(5)

            did_document = await did.resolve()

            did_document_dict = did_document.get_json_payload()
            assert did_document_dict == {
                "@context": "https://www.w3.org/ns/did/v1",
                "assertionMethod": [f"{did.identifier}#did-root-key"],
                "authentication": [f"{did.identifier}#did-root-key"],
                "id": did.identifier,
                "verificationMethod": [
                    {
                        "controller": did.identifier,
                        "id": f"{did.identifier}#did-root-key",
                        "publicKeyBase58": bytes_to_b58(bytes(OPERATOR_KEY.public_key().to_bytes_raw())),
                        "type": OPERATOR_KEY_TYPE,
                    },
                ],
            }

            did_topic_messages = await resolve_did_topic_messages(did.topic_id, client)
            assert len(did_topic_messages) == 3
