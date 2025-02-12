import datetime
import time
from enum import StrEnum
from typing import cast

from hiero_sdk_python import Client, Timestamp

from ..did.utils import parse_identifier
from ..hcs.hcs_message_resolver import HcsMessageResolver
from ..utils.cache import Cache, MemoryCache, TimestampedRecord
from .did_document import DidDocument
from .did_error import DidErrorCode, DidException
from .hcs.hcs_did_message import HcsDidMessage, HcsDidMessageEnvelope
from .hedera_did import HederaDid
from .types import DIDDocument, DIDDocumentMetadata, DIDResolutionResult

INSERTION_THRESHOLD_SECONDS = float(10)


class DidResolutionError(StrEnum):
    """Enum for DID resolution errors"""

    """
    The resolver has failed to construct the DID document.
    This can be caused by a network issue, a wrong registry address or malformed logs while parsing the registry history.
    Please inspect the `DIDResolutionMetadata.message` to debug further.
    """
    NOT_FOUND = "notFound"

    """
    The resolver does not know how to resolve the given DID. Most likely it is not a `did:hedera`.
    """
    INVALID_DID = "invalidDid"

    """
    The resolver is misconfigured or is being asked to resolve a DID anchored on an unknown network
    """
    UNKNOWN_NETWORK = "unknownNetwork"

    """
    Unknown resolution error
    """
    UNKNOWN = "unknown"


def _get_error_description(error: Exception):
    if not isinstance(error, DidException):
        return DidResolutionError.UNKNOWN.value

    match error.code:
        case DidErrorCode.INVALID_DID_STRING:
            return DidResolutionError.INVALID_DID.value
        case DidErrorCode.INVALID_NETWORK:
            return DidResolutionError.UNKNOWN_NETWORK.value
        case DidErrorCode.DID_NOT_FOUND:
            return DidResolutionError.NOT_FOUND.value
        case _:
            return DidResolutionError.UNKNOWN.value


class HederaDidResolver:
    """Hedera DID Resolver implementation.

    Args:
        client: Hedera Client
        cache_instance: Custom cache instance. If not provided, in-memory cache is used
    """

    def __init__(
        self,
        client: Client,
        cache_instance: Cache[str, TimestampedRecord[DidDocument]] | None = None,
    ):
        self._client = client
        self._cache = cache_instance or MemoryCache[str, TimestampedRecord[DidDocument]]()

    async def resolve(self, did: str) -> DIDResolutionResult:
        """
        Resolve DID document by identifier.

        Args:
            did: DID identifier to resolve

        Returns:
            object: DID resolution result
        """
        try:
            parsed_identifier = parse_identifier(did)
            topic_id = parsed_identifier.topic_id

            timestamped_record: TimestampedRecord | None = self._cache.get(topic_id)

            if timestamped_record:
                now = time.time()
                last_updated_timestamp: float = timestamped_record.timestamp
                did_document: DidDocument = timestamped_record.data

                if (now - last_updated_timestamp) > INSERTION_THRESHOLD_SECONDS:
                    result = await HcsMessageResolver(
                        topic_id,
                        HcsDidMessageEnvelope,
                        timestamp_from=Timestamp(int(last_updated_timestamp), 0),
                    ).execute(self._client)

                    messages = [
                        cast(HcsDidMessage, envelope.message) for envelope in cast(list[HcsDidMessageEnvelope], result)
                    ]

                    await did_document.process_messages(messages)

                    self._cache.set(
                        topic_id,
                        TimestampedRecord(did_document, did_document.updated or did_document.created or time.time()),
                    )
            else:
                registered_did = HederaDid(identifier=did, client=self._client)

                did_document = await registered_did.resolve()

                self._cache.set(
                    topic_id,
                    TimestampedRecord(did_document, did_document.updated or did_document.created or time.time()),
                )

            document_meta = {
                "versionId": did_document.version_id,
            }

            if not did_document.deactivated:
                document_meta.update({
                    "created": datetime.date.fromtimestamp(cast(float, did_document.created)).isoformat(),
                    "updated": datetime.date.fromtimestamp(cast(float, did_document.updated)).isoformat(),
                })

            status = {"deactivated": True} if did_document.deactivated else {}

            return {
                "didDocumentMetadata": cast(DIDDocumentMetadata, {**status, **document_meta}),
                "didResolutionMetadata": {"contentType": "application/did+ld+json"},
                "didDocument": cast(DIDDocument, did_document.get_json_payload()),
            }
        except Exception as error:
            return {
                "didResolutionMetadata": {
                    "error": _get_error_description(error),
                    "message": str(error),  # pyright: ignore - this is not in spec, but may be helpful
                },
                "didDocumentMetadata": {},
                "didDocument": None,
            }
