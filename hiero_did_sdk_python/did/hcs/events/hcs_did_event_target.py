from enum import StrEnum


class HcsDidEventTarget(StrEnum):
    DID_DOCUMENT = "DIDDocument"
    DID_OWNER = "DIDOwner"
    VERIFICATION_METHOD = "VerificationMethod"
    VERIFICATION_RELATIONSHIP = "VerificationRelationship"
    SERVICE = "Service"
    DOCUMENT = "Document"
