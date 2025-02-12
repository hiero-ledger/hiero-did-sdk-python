from dataclasses import dataclass

from hiero_sdk_python import (
    Client,
    Hbar,
    PrivateKey,
    PublicKey,
    TopicCreateTransaction,
    TopicId,
    TopicInfoQuery,
    TopicUpdateTransaction,
)
from hiero_sdk_python.consensus.topic_info import TopicInfo

from .constants import MAX_TRANSACTION_FEE
from .utils import execute_hcs_query_async, execute_hcs_transaction_async, sign_hcs_transaction_async

TopicTransaction = TopicCreateTransaction | TopicUpdateTransaction


@dataclass(frozen=True)
class HcsTopicOptions:
    submit_key: PublicKey
    topic_memo: str | None = None
    admin_key: PublicKey | None = None
    max_transaction_fee_hbar: int | None = None


def _set_topic_transaction_options(transaction: TopicTransaction, topic_options: HcsTopicOptions) -> TopicTransaction:
    if topic_options.admin_key:
        transaction.set_admin_key(topic_options.admin_key)

    if topic_options.topic_memo:
        transaction.set_memo(topic_options.topic_memo)

    max_transaction_fee = (
        Hbar(topic_options.max_transaction_fee_hbar) if topic_options.max_transaction_fee_hbar else MAX_TRANSACTION_FEE
    )
    transaction.transaction_fee = max_transaction_fee.to_tinybars()

    transaction.set_submit_key(topic_options.submit_key)

    return transaction


class HcsTopicService:
    def __init__(self, client: Client):
        self._client = client

    async def create_topic(self, topic_options: HcsTopicOptions, signing_keys: list[PrivateKey]) -> str:
        transaction = _set_topic_transaction_options(TopicCreateTransaction(), topic_options).freeze_with(self._client)

        signed_transaction = await sign_hcs_transaction_async(transaction, signing_keys)
        transaction_receipt = await execute_hcs_transaction_async(signed_transaction, self._client)

        return str(transaction_receipt.topicId)

    async def update_topic(self, topic_id: str, topic_options: HcsTopicOptions, signing_keys: list[PrivateKey]):
        transaction = _set_topic_transaction_options(
            TopicUpdateTransaction(topic_id=TopicId.from_string(topic_id)), topic_options
        ).freeze_with(self._client)
        signed_transaction = await sign_hcs_transaction_async(transaction, signing_keys)
        await execute_hcs_transaction_async(signed_transaction, self._client)

    async def get_topic_info(self, topic_id: str) -> TopicInfo:
        return await execute_hcs_query_async(TopicInfoQuery(topic_id=TopicId.from_string(topic_id)), self._client)
