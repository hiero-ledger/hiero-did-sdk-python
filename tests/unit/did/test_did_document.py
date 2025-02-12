from unittest.mock import patch

import pytest
from hiero_sdk_python import PrivateKey

from hiero_did_sdk_python.did.did_document import DidDocument
from hiero_did_sdk_python.did.did_document_operation import DidDocumentOperation
from hiero_did_sdk_python.did.hcs.events.document.hcs_did_create_did_document_event import HcsDidCreateDidDocumentEvent
from hiero_did_sdk_python.did.hcs.events.document.hcs_did_delete_event import HcsDidDeleteEvent
from hiero_did_sdk_python.did.hcs.events.owner.hcs_did_update_did_owner_event import HcsDidUpdateDidOwnerEvent
from hiero_did_sdk_python.did.hcs.events.service.hcs_did_update_service_event import HcsDidUpdateServiceEvent
from hiero_did_sdk_python.did.hcs.events.verification_method.hcs_did_update_verification_method_event import (
    HcsDidUpdateVerificationMethodEvent,
)
from hiero_did_sdk_python.did.hcs.events.verification_relationship.hcs_did_update_verification_relationship_event import (
    HcsDidUpdateVerificationRelationshipEvent,
)
from hiero_did_sdk_python.did.hcs.hcs_did_message import HcsDidMessage
from hiero_did_sdk_python.utils.encoding import bytes_to_b58, multibase_encode
from hiero_did_sdk_python.utils.keys import get_key_type

from .common import IDENTIFIER_2, PRIVATE_KEY_ARR


class TestDidDocument:
    def test_to_json_tree(self):
        """returns empty document if not events were passed"""
        doc = DidDocument(IDENTIFIER_2)

        assert doc.get_json_payload() == {
            "@context": "https://www.w3.org/ns/did/v1",
            "assertionMethod": [],
            "authentication": [],
            "id": IDENTIFIER_2,
            "verificationMethod": [],
        }

        assert doc.created is None
        assert doc.updated is None
        assert not doc.deactivated
        assert doc.version_id is None

    @pytest.mark.asyncio
    async def test_ignores_till_create(self, test_key):
        """ignores events til first create DIDOwner event"""
        doc = DidDocument(IDENTIFIER_2)

        await doc.process_messages([
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateServiceEvent(f"{IDENTIFIER_2}#service-1", "LinkedDomains", "https://test.identity.com"),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateDidOwnerEvent(
                    f"{IDENTIFIER_2}#did-root-key", IDENTIFIER_2, test_key.public_key, test_key.key_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateServiceEvent(f"{IDENTIFIER_2}#service-2", "LinkedDomains", "https://test2.identity.com"),
            ),
        ])

        assert doc.get_json_payload() == {
            "@context": "https://www.w3.org/ns/did/v1",
            "id": IDENTIFIER_2,
            "assertionMethod": [f"{IDENTIFIER_2}#did-root-key"],
            "authentication": [f"{IDENTIFIER_2}#did-root-key"],
            "service": [
                {
                    "id": f"{IDENTIFIER_2}#service-2",
                    "serviceEndpoint": "https://test2.identity.com",
                    "type": "LinkedDomains",
                }
            ],
            "verificationMethod": [
                {
                    "controller": IDENTIFIER_2,
                    "id": f"{IDENTIFIER_2}#did-root-key",
                    "publicKeyBase58": test_key.public_key_base58,
                    "type": test_key.key_type,
                }
            ],
        }
        assert doc.created
        assert doc.updated
        assert not doc.deactivated
        assert doc.version_id

    @patch("hiero_did_sdk_python.did.did_document.download_ipfs_document_by_cid")
    @pytest.mark.asyncio
    async def test_handle_did_create_doc_event(self, mock_download_ipfs_document_by_cid, test_key):
        """handles HcsDidCreateDidDocumentEvent events"""
        messages = [
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidCreateDidDocumentEvent(f"{IDENTIFIER_2}#did-document", "Qm123456"),
            )
        ]

        doc = DidDocument(IDENTIFIER_2)

        test_doc = {
            "@context": "https://www.w3.org/ns/did/v1",
            "assertionMethod": [f"{IDENTIFIER_2}#did-root-key"],
            "authentication": [f"{IDENTIFIER_2}#did-root-key"],
            "id": IDENTIFIER_2,
            "service": [
                {
                    "id": f"{IDENTIFIER_2}#service-1",
                    "serviceEndpoint": "https://example.com/vcs",
                    "type": "LinkedDomains",
                }
            ],
            "verificationMethod": [
                {
                    "controller": IDENTIFIER_2,
                    "id": f"{IDENTIFIER_2}#did-root-key",
                    "publicKeyMultibase": test_key.public_key_base58_multibase,
                    "type": test_key.key_type,
                }
            ],
            "controller": {},
        }

        mock_download_ipfs_document_by_cid.return_value = test_doc

        await doc.process_messages(messages)

        del test_doc["controller"]

        assert doc.get_json_payload() == test_doc

    @pytest.mark.asyncio
    async def test_handles_ceate_didowner_event(self, test_key):
        """handles create DIDOwner event"""

        messages = [
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateDidOwnerEvent(
                    f"{IDENTIFIER_2}#did-root-key", IDENTIFIER_2, test_key.public_key, test_key.key_type
                ),
            )
        ]

        doc = DidDocument(IDENTIFIER_2)

        await doc.process_messages(messages)

        assert doc.get_json_payload() == {
            "@context": "https://www.w3.org/ns/did/v1",
            "assertionMethod": [f"{IDENTIFIER_2}#did-root-key"],
            "authentication": [f"{IDENTIFIER_2}#did-root-key"],
            "id": IDENTIFIER_2,
            "verificationMethod": [
                {
                    "controller": IDENTIFIER_2,
                    "id": f"{IDENTIFIER_2}#did-root-key",
                    "publicKeyBase58": test_key.public_key_base58,
                    "type": test_key.key_type,
                }
            ],
        }
        assert doc.created
        assert doc.updated
        assert not doc.deactivated
        assert doc.version_id

    @pytest.mark.asyncio
    async def test_handle_did_delete_event(self, test_key):
        """handles DID delete event"""

        messages = [
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateDidOwnerEvent(
                    f"{IDENTIFIER_2}#did-root-key", IDENTIFIER_2, test_key.public_key, test_key.key_type
                ),
            ),
            HcsDidMessage(DidDocumentOperation.DELETE, IDENTIFIER_2, HcsDidDeleteEvent()),
        ]

        doc = DidDocument(IDENTIFIER_2)

        await doc.process_messages(messages)

        assert doc.get_json_payload() == {
            "@context": "https://www.w3.org/ns/did/v1",
            "assertionMethod": [],
            "authentication": [],
            "id": IDENTIFIER_2,
            "verificationMethod": [],
        }
        assert doc.created is None
        assert doc.updated is None
        assert doc.deactivated
        assert doc.version_id is None

    @pytest.mark.asyncio
    async def test_handle_change_did_owner_event(self, test_key):
        """handles change DID owner event"""
        other_owner_key = PrivateKey.generate()
        other_owner_identifier = f"did:hedera:testnet:{multibase_encode(bytes(other_owner_key.public_key().to_bytes_raw()), "base58btc")}_0.0.29999999"

        key2 = PrivateKey.generate()
        key2_type = get_key_type(key2)

        messages = [
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateDidOwnerEvent(
                    f"{IDENTIFIER_2}#did-root-key", IDENTIFIER_2, test_key.public_key, test_key.key_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateVerificationRelationshipEvent(
                    f"{IDENTIFIER_2}#key-2",
                    key2.public_key(),
                    IDENTIFIER_2,
                    "capabilityDelegation",
                    key2_type,
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.UPDATE,
                IDENTIFIER_2,
                HcsDidUpdateDidOwnerEvent(
                    f"{other_owner_identifier}#did-root-key",
                    other_owner_identifier,
                    test_key.public_key,
                    test_key.key_type,
                ),
            ),
        ]

        doc = DidDocument(IDENTIFIER_2)

        await doc.process_messages(messages)

        assert doc.get_json_payload() == {
            "@context": "https://www.w3.org/ns/did/v1",
            "assertionMethod": [f"{other_owner_identifier}#did-root-key"],
            "authentication": [f"{other_owner_identifier}#did-root-key"],
            "capabilityDelegation": [f"{IDENTIFIER_2}#key-2"],
            "controller": other_owner_identifier,
            "id": IDENTIFIER_2,
            "verificationMethod": [
                {
                    "controller": other_owner_identifier,
                    "id": f"{other_owner_identifier}#did-root-key",
                    "publicKeyBase58": test_key.public_key_base58,
                    "type": test_key.key_type,
                },
                {
                    "controller": IDENTIFIER_2,
                    "id": f"{IDENTIFIER_2}#key-2",
                    "publicKeyBase58": bytes_to_b58(bytes(key2.public_key().to_bytes_raw())),
                    "type": key2_type,
                },
            ],
        }
        assert doc.created
        assert doc.updated
        assert not doc.deactivated
        assert doc.version_id

    @pytest.mark.asyncio
    async def test_handle_add_ver_rel_events(self, test_key):
        """successfully handles add service, verificationMethod and verificationRelationship events"""
        key1 = PrivateKey.generate()
        key1_type = get_key_type(key1)

        key2 = PrivateKey.generate()
        key2_type = get_key_type(key2)

        messages = [
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateDidOwnerEvent(
                    f"{IDENTIFIER_2}#did-root-key", IDENTIFIER_2, test_key.public_key, test_key.key_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateServiceEvent(f"{IDENTIFIER_2}#service-1", "LinkedDomains", "https://test.identity.com"),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateVerificationMethodEvent(
                    f"{IDENTIFIER_2}#key-1", IDENTIFIER_2, key1.public_key(), key1_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateVerificationRelationshipEvent(
                    f"{IDENTIFIER_2}#key-2", key2.public_key(), IDENTIFIER_2, "capabilityDelegation", key2_type
                ),
            ),
        ]

        doc = DidDocument(IDENTIFIER_2)

        await doc.process_messages(messages)

        assert doc.get_json_payload() == {
            "@context": "https://www.w3.org/ns/did/v1",
            "assertionMethod": [f"{IDENTIFIER_2}#did-root-key"],
            "authentication": [f"{IDENTIFIER_2}#did-root-key"],
            "capabilityDelegation": [f"{IDENTIFIER_2}#key-2"],
            "id": IDENTIFIER_2,
            "service": [
                {
                    "id": f"{IDENTIFIER_2}#service-1",
                    "serviceEndpoint": "https://test.identity.com",
                    "type": "LinkedDomains",
                }
            ],
            "verificationMethod": [
                {
                    "controller": IDENTIFIER_2,
                    "id": f"{IDENTIFIER_2}#did-root-key",
                    "publicKeyBase58": test_key.public_key_base58,
                    "type": test_key.key_type,
                },
                {
                    "controller": IDENTIFIER_2,
                    "id": f"{IDENTIFIER_2}#key-1",
                    "publicKeyBase58": bytes_to_b58(bytes(key1.public_key().to_bytes_raw())),
                    "type": key1_type,
                },
                {
                    "controller": IDENTIFIER_2,
                    "id": f"{IDENTIFIER_2}#key-2",
                    "publicKeyBase58": bytes_to_b58(bytes(key2.public_key().to_bytes_raw())),
                    "type": key2_type,
                },
            ],
        }
        assert doc.created
        assert doc.updated
        assert not doc.deactivated
        assert doc.version_id

    @pytest.mark.asyncio
    async def test_handle_update_ver_rel(self, test_key):
        """successfully handles update service, verificationMethod and verificationRelationship events"""
        key1 = PRIVATE_KEY_ARR[0]
        key1_type = get_key_type(key1)

        key2 = PRIVATE_KEY_ARR[1]
        key2_type = get_key_type(key2)

        key3 = PRIVATE_KEY_ARR[2]
        key3_type = get_key_type(key3)

        key4 = PRIVATE_KEY_ARR[3]
        key4_type = get_key_type(key4)

        key5 = PRIVATE_KEY_ARR[4]
        key5_type = get_key_type(key5)

        messages = [
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateDidOwnerEvent(
                    f"{IDENTIFIER_2}#did-root-key", IDENTIFIER_2, test_key.public_key, test_key.key_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateServiceEvent(f"{IDENTIFIER_2}#service-1", "LinkedDomains", "https://test.identity.com"),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateServiceEvent(f"{IDENTIFIER_2}#service-2", "LinkedDomains", "https://test2.identity.com"),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateVerificationMethodEvent(
                    f"{IDENTIFIER_2}#key-1", IDENTIFIER_2, key1.public_key(), key1_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateVerificationRelationshipEvent(
                    f"{IDENTIFIER_2}#key-2", key2.public_key(), IDENTIFIER_2, "capabilityDelegation", key2_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateVerificationRelationshipEvent(
                    f"{IDENTIFIER_2}#key-3", key3.public_key(), IDENTIFIER_2, "authentication", key3_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.UPDATE,
                IDENTIFIER_2,
                HcsDidUpdateServiceEvent(f"{IDENTIFIER_2}#service-1", "LinkedDomains", "https://new.test.identity.com"),
            ),
            HcsDidMessage(
                DidDocumentOperation.UPDATE,
                IDENTIFIER_2,
                HcsDidUpdateVerificationMethodEvent(
                    f"{IDENTIFIER_2}#key-1", IDENTIFIER_2, key4.public_key(), key4_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.UPDATE,
                IDENTIFIER_2,
                HcsDidUpdateVerificationRelationshipEvent(
                    f"{IDENTIFIER_2}#key-2", key5.public_key(), IDENTIFIER_2, "capabilityDelegation", key5_type
                ),
            ),
        ]

        doc = DidDocument(IDENTIFIER_2)

        await doc.process_messages(messages)

        assert doc.get_json_payload() == {
            "@context": "https://www.w3.org/ns/did/v1",
            "assertionMethod": [f"{IDENTIFIER_2}#did-root-key"],
            "authentication": [f"{IDENTIFIER_2}#did-root-key", f"{IDENTIFIER_2}#key-3"],
            "capabilityDelegation": [f"{IDENTIFIER_2}#key-2"],
            "id": IDENTIFIER_2,
            "service": [
                {
                    "id": f"{IDENTIFIER_2}#service-1",
                    "serviceEndpoint": "https://new.test.identity.com",
                    "type": "LinkedDomains",
                },
                {
                    "id": f"{IDENTIFIER_2}#service-2",
                    "serviceEndpoint": "https://test2.identity.com",
                    "type": "LinkedDomains",
                },
            ],
            "verificationMethod": [
                {
                    "controller": IDENTIFIER_2,
                    "id": f"{IDENTIFIER_2}#did-root-key",
                    "publicKeyBase58": test_key.public_key_base58,
                    "type": test_key.key_type,
                },
                {
                    "controller": IDENTIFIER_2,
                    "id": f"{IDENTIFIER_2}#key-1",
                    "publicKeyBase58": bytes_to_b58(bytes(key4.public_key().to_bytes_raw())),
                    "type": key4_type,
                },
                {
                    "controller": IDENTIFIER_2,
                    "id": f"{IDENTIFIER_2}#key-2",
                    "publicKeyBase58": bytes_to_b58(bytes(key5.public_key().to_bytes_raw())),
                    "type": key5_type,
                },
                {
                    "controller": IDENTIFIER_2,
                    "id": f"{IDENTIFIER_2}#key-3",
                    "publicKeyBase58": bytes_to_b58(bytes(key3.public_key().to_bytes_raw())),
                    "type": key3_type,
                },
            ],
        }
        assert doc.created
        assert doc.updated
        assert not doc.deactivated
        assert doc.version_id

    @pytest.mark.asyncio
    async def test_handle_revoke_ver_rel(self, test_key):
        """successfully handles revoke service, verificationMethod and verificationRelationship events"""
        key1 = PrivateKey.generate()
        key1_type = get_key_type(key1)

        key2 = PrivateKey.generate()
        key2_type = get_key_type(key2)

        key3 = PrivateKey.generate()
        key3_type = get_key_type(key3)

        messages = [
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateDidOwnerEvent(
                    f"{IDENTIFIER_2}#did-root-key", IDENTIFIER_2, test_key.public_key, test_key.key_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateServiceEvent(f"{IDENTIFIER_2}#service-1", "LinkedDomains", "https://test.identity.com"),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateServiceEvent(f"{IDENTIFIER_2}#service-2", "LinkedDomains", "https://test2.identity.com"),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateVerificationMethodEvent(
                    f"{IDENTIFIER_2}#key-1", IDENTIFIER_2, key1.public_key(), key1_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateVerificationRelationshipEvent(
                    f"{IDENTIFIER_2}#key-2", key2.public_key(), IDENTIFIER_2, "capabilityDelegation", key2_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.CREATE,
                IDENTIFIER_2,
                HcsDidUpdateVerificationRelationshipEvent(
                    f"{IDENTIFIER_2}#key-3", key3.public_key(), IDENTIFIER_2, "authentication", key3_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.REVOKE,
                IDENTIFIER_2,
                HcsDidUpdateServiceEvent(f"{IDENTIFIER_2}#service-1", "LinkedDomains", "https://test.identity.com"),
            ),
            HcsDidMessage(
                DidDocumentOperation.REVOKE,
                IDENTIFIER_2,
                HcsDidUpdateVerificationMethodEvent(
                    f"{IDENTIFIER_2}#key-1", IDENTIFIER_2, key1.public_key(), key1_type
                ),
            ),
            HcsDidMessage(
                DidDocumentOperation.REVOKE,
                IDENTIFIER_2,
                HcsDidUpdateVerificationRelationshipEvent(
                    f"{IDENTIFIER_2}#key-2", key2.public_key(), IDENTIFIER_2, "capabilityDelegation", key2_type
                ),
            ),
        ]

        doc = DidDocument(IDENTIFIER_2)

        await doc.process_messages(messages)

        assert doc.get_json_payload() == {
            "@context": "https://www.w3.org/ns/did/v1",
            "assertionMethod": [f"{IDENTIFIER_2}#did-root-key"],
            "authentication": [f"{IDENTIFIER_2}#did-root-key", f"{IDENTIFIER_2}#key-3"],
            "id": IDENTIFIER_2,
            "service": [
                {
                    "id": f"{IDENTIFIER_2}#service-2",
                    "serviceEndpoint": "https://test2.identity.com",
                    "type": "LinkedDomains",
                }
            ],
            "verificationMethod": [
                {
                    "controller": IDENTIFIER_2,
                    "id": f"{IDENTIFIER_2}#did-root-key",
                    "publicKeyBase58": test_key.public_key_base58,
                    "type": test_key.key_type,
                },
                {
                    "controller": IDENTIFIER_2,
                    "id": f"{IDENTIFIER_2}#key-3",
                    "publicKeyBase58": bytes_to_b58(bytes(key3.public_key().to_bytes_raw())),
                    "type": key3_type,
                },
            ],
        }
        assert doc.created
        assert doc.updated
        assert not doc.deactivated
        assert doc.version_id
