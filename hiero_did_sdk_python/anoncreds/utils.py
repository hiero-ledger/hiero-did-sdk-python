from dataclasses import dataclass
from enum import StrEnum

from ..did.utils import parse_identifier
from ..utils.validation_result import ValidationResult

ANONCREDS_IDENTIFIER_SEPARATOR = "/"

ANONCREDS_OBJECT_FAMILY = "anoncreds"
ANONCREDS_VERSION = "v0"


class AnonCredsObjectType(StrEnum):
    SCHEMA = "SCHEMA"
    PUBLIC_CRED_DEF = "PUBLIC_CRED_DEF"
    REV_REG = "REV_REG"
    REV_REG_ENTRY = "REV_REG_ENTRY"


@dataclass(frozen=True)
class ParsedAnoncredsIdentifier:
    publisher_did: str
    topic_id: str
    object_type: AnonCredsObjectType


def parse_anoncreds_identifier(identifier: str) -> ParsedAnoncredsIdentifier:
    try:
        issuer_id, object_family, object_family_version, object_family_type, topic_id = identifier.split(
            ANONCREDS_IDENTIFIER_SEPARATOR
        )
    except Exception as split_error:
        raise Exception("Identifier has invalid structure") from split_error

    if object_family != ANONCREDS_OBJECT_FAMILY or object_family_version != ANONCREDS_VERSION:
        raise Exception(
            f"Identifier contains invalid object definition: {ANONCREDS_IDENTIFIER_SEPARATOR.join([object_family, object_family_version])}"
        )

    if object_family_type not in AnonCredsObjectType:
        raise Exception(f"Invalid AnonCreds object type: {object_family_type}")

    try:
        parse_identifier(issuer_id)
    except Exception as issuer_id_error:
        raise Exception(f"Cannot parse issuer identifier: {issuer_id_error}") from issuer_id_error

    return ParsedAnoncredsIdentifier(issuer_id, topic_id, AnonCredsObjectType(object_family_type))


def validate_anoncreds_identifier(identifier: str) -> ValidationResult:
    try:
        parse_anoncreds_identifier(identifier)
        return ValidationResult(is_valid=True)
    except Exception as parsing_error:
        return ValidationResult(is_valid=False, error=str(parsing_error))


def build_anoncreds_identifier(publisher_did: str, topic_id: str, object_type: AnonCredsObjectType) -> str:
    return ANONCREDS_IDENTIFIER_SEPARATOR.join([
        publisher_did,
        ANONCREDS_OBJECT_FAMILY,
        ANONCREDS_VERSION,
        object_type,
        topic_id,
    ])
