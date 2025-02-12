from hashlib import sha256
from pathlib import Path
from unittest.mock import NonCallableMagicMock

import pytest
from hiero_sdk_python import Client
from pytest_mock import MockerFixture

from hiero_did_sdk_python.hcs import (
    HcsFileChunkMessage,
    HcsFileService,
    HcsMessageResolver,
    HcsMessageTransaction,
    HcsTopicOptions,
    HcsTopicService,
)
from hiero_did_sdk_python.hcs.hcs_file import get_file_chunk_messages
from tests.integration.conftest import OPERATOR_KEY_DER

MOCK_TOPIC_ID = "0.0.1"

MOCK_CHUNK_MESSAGES = [
    HcsFileChunkMessage(
        0,
        "data:application/json;base64,KLUv/WBQAZUKACaZPhqAKc0BUmRjIzmfou0kBKXnwyhjwgb0BjQLMDYANgA3AHZCZfosvSPWKWaJ46vzkNVTqXBzQ6UUaIE37sFO7sdLNSUaic8QKYE+Vfw1IYNKT97xHidEEGbzQh60OJ88ocleGk6yjHvKOkUFnYNIy5gsaPEsx3vCEuheok+dCvdkY3IlCjr3dPFcrFSoYmhHAy1OEqpTWUL9kRIN2VsmyRO80LJ0VGnxlbgbG62ETpVw9J4DLYrZuI1LbhglLo9jJLaau1UAAQXWD2mjv9tJNJ+Xk8VsuKHn5toNEWQ0G+OjdpQMWlxeSmJ+qCMu76noEkuzGy1GaNGTJTkhIBCGmKM+abHchNqWJOA4YUgHBFO3P4Iwrrlpl69COfdK6a/dAbtd1YDOdtdIwLFaEDNwidIZx1DjZwJcOdLYcprkFtsCelo3xvARCv5ayWH93ro9",
    )
]
MOCK_PAYLOAD_HASH = "ea4d17b8c0cf44c215ade6b4ad36832672ea3188b1dad12b68c2472dfbcdeff1"
MOCK_TOPIC_MEMO = f"{MOCK_PAYLOAD_HASH}:zstd:base64"


@pytest.fixture
def mock_hcs_message_transaction(mocker: MockerFixture):
    MockHcsMessageTransaction = mocker.patch(
        "hiero_did_sdk_python.hcs.hcs_file.hcs_file_service.HcsMessageTransaction", autospec=HcsMessageTransaction
    )

    mock_hcs_message_transaction = MockHcsMessageTransaction.return_value
    mock_hcs_message_transaction.execute = mocker.AsyncMock()

    return mock_hcs_message_transaction


@pytest.fixture
def mock_hcs_topic_service(mocker: MockerFixture):
    MockHcsTopicService = mocker.patch(
        "hiero_did_sdk_python.hcs.hcs_file.hcs_file_service.HcsTopicService", autospec=HcsTopicService
    )

    mock_hsc_topic_service = MockHcsTopicService.return_value
    mock_hsc_topic_service.create_topic.return_value = MOCK_TOPIC_ID
    mock_hsc_topic_service.get_topic_info.return_value.memo = MOCK_TOPIC_MEMO

    return mock_hsc_topic_service


@pytest.fixture
def mock_hcs_message_resolver(mocker: MockerFixture):
    MockHcsMessageResolver = mocker.patch(
        "hiero_did_sdk_python.hcs.hcs_file.hcs_file_service.HcsMessageResolver", autospec=HcsMessageResolver
    )

    mock_hcs_message_resolver = MockHcsMessageResolver.return_value
    mock_hcs_message_resolver.execute.return_value = MOCK_CHUNK_MESSAGES

    return mock_hcs_message_resolver


@pytest.mark.asyncio(loop_scope="session")
class TestHcsFileService:
    @pytest.mark.parametrize(
        "test_file_path, expected_chunks_count",
        [("./tests/test_data/test_file.txt", 1), ("./tests/test_data/test_file_large.txt", 6)],
    )
    async def test_creates_topic_id_and_submits_messages(
        self,
        test_file_path: str,
        expected_chunks_count: int,
        mock_client: Client,
        mock_hcs_topic_service: NonCallableMagicMock,
        mock_hcs_message_transaction: NonCallableMagicMock,
        Something,
    ):
        file_payload = Path(test_file_path).read_bytes()
        service = HcsFileService(mock_client)

        topic_id = await service.submit_file(file_payload, OPERATOR_KEY_DER)
        assert topic_id == MOCK_TOPIC_ID

        mock_hcs_topic_service.create_topic.assert_awaited()
        mock_hcs_topic_service.create_topic.assert_awaited_with(
            HcsTopicOptions(submit_key=Something, topic_memo=Something), [Something]
        )

        assert mock_hcs_message_transaction.execute.await_count == expected_chunks_count

    async def test_resolves_messages_from_topic(
        self,
        mock_client: Client,
        mock_hcs_topic_service: NonCallableMagicMock,
        mock_hcs_message_resolver: NonCallableMagicMock,
    ):
        service = HcsFileService(mock_client)

        payload = await service.resolve_file(MOCK_TOPIC_ID)

        assert payload
        assert sha256(payload).hexdigest() == MOCK_PAYLOAD_HASH

        mock_hcs_topic_service.get_topic_info.assert_awaited_once()
        mock_hcs_topic_service.get_topic_info.assert_awaited_with(MOCK_TOPIC_ID)

        mock_hcs_message_resolver.execute.assert_awaited_once()

    async def test_throws_on_resolving_file_with_wrong_hash(
        self,
        mock_client: Client,
        mock_hcs_topic_service: NonCallableMagicMock,
        mock_hcs_message_resolver: NonCallableMagicMock,
    ):
        mock_hcs_message_resolver.execute.return_value = get_file_chunk_messages(b"invalid_payload")

        service = HcsFileService(mock_client)
        with pytest.raises(Exception, match="Resolved HCS file payload is invalid"):
            await service.resolve_file(MOCK_TOPIC_ID)

        mock_hcs_topic_service.get_topic_info.assert_awaited_once()
        mock_hcs_topic_service.get_topic_info.assert_awaited_with(MOCK_TOPIC_ID)

        mock_hcs_message_resolver.execute.assert_awaited_once()

    async def test_throws_on_resolving_invalid_topic_id(
        self, mock_client: Client, mock_hcs_topic_service: NonCallableMagicMock
    ):
        service = HcsFileService(mock_client)
        with pytest.raises(
            Exception,
            match="Invalid TopicId format. Expected 'shard.realm.num'",
        ):
            await service.resolve_file("invalid_topic_id")

        mock_hcs_topic_service.get_topic_info.assert_awaited_once()
        mock_hcs_topic_service.get_topic_info.assert_awaited_with("invalid_topic_id")

    async def test_throws_on_resolving_invalid_topic_memo(
        self, mock_client: Client, mock_hcs_topic_service, mock_hcs_message_resolver
    ):
        mock_hcs_topic_service.get_topic_info.return_value.memo = "invalid_topic_memo"

        service = HcsFileService(mock_client)
        with pytest.raises(
            Exception,
            match=f"HCS file Topic '{MOCK_TOPIC_ID}' is invalid - must contain memo compliant with HCS-1 standard",
        ):
            await service.resolve_file(MOCK_TOPIC_ID)

        mock_hcs_topic_service.get_topic_info.assert_awaited_once()
        mock_hcs_topic_service.get_topic_info.assert_awaited_with(MOCK_TOPIC_ID)

        mock_hcs_message_resolver.execute.assert_not_awaited()
