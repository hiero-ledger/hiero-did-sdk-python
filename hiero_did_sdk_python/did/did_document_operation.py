from enum import StrEnum


class DidDocumentOperation(StrEnum):
    CREATE = "create"
    CREATE_DID_DOCUMENT = "create-did-document"
    UPDATE = "update"
    DELETE = "delete"
    REVOKE = "revoke"
