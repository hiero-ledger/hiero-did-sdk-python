import logging
import re
from hashlib import sha256
from typing import cast

from hiero_sdk_python import Client, PrivateKey, TopicMessageSubmitTransaction
from hiero_sdk_python.transaction.transaction import Transaction

from ..constants import MAX_TRANSACTION_FEE
from ..hcs_message_resolver import HcsMessageResolver
from ..hcs_message_transaction import HcsMessageTransaction
from ..hcs_topic_service import HcsTopicOptions, HcsTopicService
from .hcs_file_chunk_message import HcsFileChunkMessage
from .utils import build_file_from_chunk_messages, get_file_chunk_messages

READ_TOPIC_MESSAGES_TIMEOUT_SECONDS = float(5)

HCS_FILE_TOPIC_MEMO_REGEX = re.compile("^[A-Fa-f0-9]{64}:zstd:base64$")

LOGGER = logging.getLogger(__name__)


class HcsFileService:
    """Provides API for managing files on Hedera HCS according to HCS-1 standard"""

    def __init__(self, client: Client):
        self._client = client
        self._hcs_topic_service = HcsTopicService(client)

    async def submit_file(self, payload: bytes, submit_key_der: str) -> str:
        """Submit new file to HCS"""
        try:
            submit_key = PrivateKey.from_string(submit_key_der)
            payload_hash = sha256(payload).hexdigest()

            topic_memo = f"{payload_hash}:zstd:base64"
            topic_options = HcsTopicOptions(submit_key=submit_key.public_key(), topic_memo=topic_memo)

            topic_id = await self._hcs_topic_service.create_topic(topic_options, [submit_key])

            chunk_messages = get_file_chunk_messages(payload)

            for message in chunk_messages:

                def build_message_submit_transaction(
                    message_submit_transaction: TopicMessageSubmitTransaction,
                ) -> Transaction:
                    message_submit_transaction.transaction_fee = MAX_TRANSACTION_FEE.to_tinybars()  # pyright: ignore [reportAttributeAccessIssue]
                    return message_submit_transaction.freeze_with(self._client).sign(submit_key)

                await HcsMessageTransaction(topic_id, message, build_message_submit_transaction).execute(self._client)

            return topic_id
        except Exception as error:
            LOGGER.error(f"Error on submitting new file to HCS: {error!s}")
            raise error

    async def resolve_file(self, topic_id: str) -> bytes | None:
        """Resolve and verify HCS file payload by Topic ID"""
        try:
            topic_info = await self._hcs_topic_service.get_topic_info(topic_id)
            topic_memo = str(topic_info.memo)

            if not topic_memo or not HCS_FILE_TOPIC_MEMO_REGEX.match(topic_memo):
                raise Exception(
                    f"HCS file Topic '{topic_id}' is invalid - must contain memo compliant with HCS-1 standard"
                )

            resolved_messages = await HcsMessageResolver(
                topic_id, HcsFileChunkMessage, READ_TOPIC_MESSAGES_TIMEOUT_SECONDS
            ).execute(self._client)

            chunk_messages = [cast(HcsFileChunkMessage, message) for message in resolved_messages]
            if len(chunk_messages) == 0:
                return None

            payload = build_file_from_chunk_messages(chunk_messages)

            expected_payload_hash, _, _ = topic_memo.split(":")
            if sha256(payload).hexdigest() != expected_payload_hash:
                raise Exception("Resolved HCS file payload is invalid")

            return payload
        except Exception as error:
            LOGGER.error(f"Error on resolving HCS file: {error!s}")
            raise error
