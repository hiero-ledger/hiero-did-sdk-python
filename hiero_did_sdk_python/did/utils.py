import re
from dataclasses import dataclass

from .did_error import DidErrorCode, DidException
from .did_syntax import (
    DID_METHOD_SEPARATOR,
    DID_PREFIX,
    DID_TOPIC_SEPARATOR,
    HEDERA_DID_METHOD,
    HEDERA_NETWORK_MAINNET,
    HEDERA_NETWORK_PREVIEWNET,
    HEDERA_NETWORK_TESTNET,
)

OWNER_KEY_POSTFIX_REGEX = re.compile(r"^(did\-root\-key)$")
SERVICE_ID_POSTFIX_REGEX = re.compile(r"^(service)\-[0-9]{1,}$")
KEY_ID_POSTFIX_REGEX = re.compile(r"^(key)\-[0-9]{1,}$")
TOPIC_ID_REGEX = re.compile(r"^[0-9]{1,}\.[0-9]{1,}\.[0-9]{1,}$")


def is_valid_did(did: str) -> bool:
    identifier, _ = did.split("#") if "#" in did else [did, ""]

    if not identifier:
        return False

    parse_identifier(identifier)
    return True


def is_owner_event_id_valid(event_id: str) -> bool:
    identifier, id_ = event_id.split("#") if "#" in event_id else [event_id, ""]

    if not identifier or not id_:
        return False

    parse_identifier(identifier)

    return bool(OWNER_KEY_POSTFIX_REGEX.match(id_))


def is_service_event_id_valid(event_id: str) -> bool:
    identifier, id_ = event_id.split("#") if "#" in event_id else [event_id, ""]

    if not identifier or not id_:
        return False

    parse_identifier(identifier)

    return bool(SERVICE_ID_POSTFIX_REGEX.match(id_))


def is_key_event_id_valid(event_id: str) -> bool:
    identifier, id_ = event_id.split("#") if "#" in event_id else [event_id, ""]

    if not identifier or not id_:
        return False

    parse_identifier(identifier)

    return bool(KEY_ID_POSTFIX_REGEX.match(id_))


@dataclass
class ParsedIdentifier:
    network: str
    topic_id: str
    public_key_base58: str


def parse_identifier(identifier: str) -> ParsedIdentifier:
    did_part, topic_id = (
        identifier.split(DID_TOPIC_SEPARATOR) if DID_TOPIC_SEPARATOR in identifier else [identifier, ""]
    )

    if not topic_id:
        raise DidException("DID string is invalid: topic ID is missing", DidErrorCode.INVALID_DID_STRING)

    did_parts = did_part.split(DID_METHOD_SEPARATOR) if DID_METHOD_SEPARATOR in did_part else [did_part, ""]

    if did_parts.pop(0) != DID_PREFIX:
        raise DidException("DID string is invalid: invalid prefix.", DidErrorCode.INVALID_DID_STRING)

    method_name = did_parts.pop(0)
    if method_name != HEDERA_DID_METHOD:
        raise DidException(
            "DID string is invalid: invalid method name: " + method_name, DidErrorCode.INVALID_DID_STRING
        )

    try:
        network_name = did_parts.pop(0)

        if (
            network_name != HEDERA_NETWORK_MAINNET
            and network_name != HEDERA_NETWORK_TESTNET
            and network_name != HEDERA_NETWORK_PREVIEWNET
        ):
            raise DidException("DID string is invalid. Invalid Hedera network.", DidErrorCode.INVALID_NETWORK)

        public_key_base58 = did_parts.pop(0)

        if len(public_key_base58) < 44 or len(did_parts) > 0:
            raise DidException("DID string is invalid. ID holds incorrect format.", DidErrorCode.INVALID_DID_STRING)

        if topic_id and not TOPIC_ID_REGEX.match(topic_id):
            raise DidException("DID string is invalid. Topic ID doesn't match pattern", DidErrorCode.INVALID_DID_STRING)

        return ParsedIdentifier(network_name, topic_id, public_key_base58)
    except Exception as error:
        if isinstance(error, DidException):
            raise error

        raise DidException("DID string is invalid. " + str(error), DidErrorCode.INVALID_DID_STRING) from error


def build_identifier(network: str, public_key: str, topic_id: str):
    network_segment = f"{HEDERA_DID_METHOD}{DID_METHOD_SEPARATOR}{network}"

    return (
        DID_PREFIX
        + DID_METHOD_SEPARATOR
        + network_segment
        + DID_METHOD_SEPARATOR
        + public_key
        + DID_TOPIC_SEPARATOR
        + topic_id
    )
