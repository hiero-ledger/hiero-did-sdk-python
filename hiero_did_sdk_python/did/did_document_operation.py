from enum import StrEnum


class DidDocumentOperation(StrEnum):
    CREATE = "create"
    UPDATE = "update"
    REVOKE = "revoke"
    DELETE = "delete"
