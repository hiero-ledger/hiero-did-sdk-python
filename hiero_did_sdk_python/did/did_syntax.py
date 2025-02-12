from enum import StrEnum

DID_PREFIX = "did"
DID_DOCUMENT_CONTEXT = "https://www.w3.org/ns/did/v1"
DID_METHOD_SEPARATOR = ":"
DID_TOPIC_SEPARATOR = "_"

HEDERA_NETWORK_MAINNET = "mainnet"
HEDERA_NETWORK_TESTNET = "testnet"
HEDERA_NETWORK_PREVIEWNET = "previewnet"

HEDERA_DID_METHOD = "hedera"


class DidDocumentJsonProperties(StrEnum):
    CONTEXT = "@context"
    ID = "id"
    CONTROLLER = "controller"
    AUTHENTICATION = "authentication"
    VERIFICATION_METHOD = "verificationMethod"
    ASSERTION_METHOD = "assertionMethod"
    KEY_AGREEMENT = "keyAgreement"
    CAPABILITY_INVOCATION = "capabilityInvocation"
    CAPABILITY_DELEGATION = "capabilityDelegation"
    SERVICE = "service"
