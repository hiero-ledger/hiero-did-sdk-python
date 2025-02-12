from enum import StrEnum


class DidErrorCode(StrEnum):
    """Enum for DID-related error codes"""

    """Generic (unknown) error"""
    GENERIC = "generic"

    """Invalid DID identifier string. Can be caused by non-Hedera DID method prefix, invalid or missing Topic ID and generally incorrect format"""
    INVALID_DID_STRING = "invalid_did_string"

    """Invalid Hedera network specified in DID identifier"""
    INVALID_NETWORK = "invalid_network"

    """Specified DID is not found"""
    DID_NOT_FOUND = "did_not_found"


class DidException(Exception):
    """Class for DID-related exceptions

    Args:
        message: Error message
        code: DID Error code
    """

    def __init__(self, message: str, code: DidErrorCode = DidErrorCode.GENERIC):
        super().__init__(message)

        self.code = code
