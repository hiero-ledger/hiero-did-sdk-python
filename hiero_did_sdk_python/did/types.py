from typing import Literal

from did_resolver import DIDDocument, DIDResolutionResult
from did_resolver.resolver import DIDDocumentMetadata

DidServiceType = Literal["LinkedDomains", "DIDCommMessaging"]

SupportedKeyType = Literal["Ed25519VerificationKey2018", "EcdsaSecp256k1VerificationKey2019"]

VerificationRelationshipType = Literal[
    "authentication", "assertionMethod", "keyAgreement", "capabilityInvocation", "capabilityDelegation"
]

__all__ = [
    "DIDResolutionResult",
    "DIDDocument",
    "DIDDocumentMetadata",
    "DidServiceType",
    "SupportedKeyType",
    "VerificationRelationshipType",
]
