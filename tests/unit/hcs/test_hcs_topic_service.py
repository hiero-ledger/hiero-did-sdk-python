from unittest.mock import NonCallableMagicMock

import pytest
from hiero_sdk_python import Client, ResponseCode
from pytest_mock import MockerFixture

from hiero_did_sdk_python.hcs import HcsTopicOptions, HcsTopicService

from ..conftest import PRIVATE_KEY

MOCK_TOPIC_MEMO = "mock-topic-memo"
MOCK_TOPIC_ID = "0.0.1"


@pytest.fixture
def mock_topic_create_transaction(mocker: MockerFixture):
    MockTopicCreateTransaction = mocker.patch("hiero_did_sdk_python.hcs.hcs_topic_service.TopicCreateTransaction")

    mock_transaction_response = mocker.MagicMock()
    mock_transaction_response.topic_id.__str__.return_value = MOCK_TOPIC_ID
    mock_transaction_response.status = ResponseCode.SUCCESS

    mock_topic_create_transaction = MockTopicCreateTransaction.return_value
    mock_topic_create_transaction.freeze_with.return_value = mock_topic_create_transaction
    mock_topic_create_transaction.sign.return_value = mock_topic_create_transaction
    mock_topic_create_transaction.execute.return_value = mock_transaction_response

    return mock_topic_create_transaction


@pytest.fixture
def mock_topic_update_transaction(mocker: MockerFixture):
    MockTopicUpdateTransaction = mocker.patch("hiero_did_sdk_python.hcs.hcs_topic_service.TopicUpdateTransaction")

    mock_transaction_response = mocker.MagicMock()
    mock_transaction_response.topic_id.__str__.return_value = MOCK_TOPIC_ID
    mock_transaction_response.status = ResponseCode.SUCCESS

    mock_topic_update_transaction = MockTopicUpdateTransaction.return_value
    mock_topic_update_transaction.freeze_with.return_value = mock_topic_update_transaction
    mock_topic_update_transaction.sign.return_value = mock_topic_update_transaction
    mock_topic_update_transaction.execute.return_value = mock_transaction_response

    return mock_topic_update_transaction


@pytest.fixture
def mock_topic_info_query(mocker: MockerFixture):
    mocker.patch("hiero_did_sdk_python.hcs.hcs_topic_service.TopicId")
    MockTopicInfoQuery = mocker.patch("hiero_did_sdk_python.hcs.hcs_topic_service.TopicInfoQuery")

    mock_topic_info_query = MockTopicInfoQuery.return_value
    mock_topic_info_query.execute.return_value.memo = MOCK_TOPIC_MEMO

    return mock_topic_info_query


@pytest.mark.asyncio(loop_scope="session")
class TestHcsTopicService:
    async def test_creates_new_topic(self, mock_client: Client, mock_topic_create_transaction: NonCallableMagicMock):
        service = HcsTopicService(mock_client)

        topic_id = await service.create_topic(
            topic_options=HcsTopicOptions(submit_key=PRIVATE_KEY.public_key(), topic_memo=MOCK_TOPIC_MEMO),
            signing_keys=[PRIVATE_KEY],
        )
        assert topic_id == MOCK_TOPIC_ID

        mock_topic_create_transaction.set_memo.assert_called_once()
        mock_topic_create_transaction.set_memo.assert_called_with(MOCK_TOPIC_MEMO)

        mock_topic_create_transaction.sign.assert_called_once()
        mock_topic_create_transaction.sign.assert_called_with(PRIVATE_KEY)

        mock_topic_create_transaction.execute.assert_called_once()
        mock_topic_create_transaction.execute.assert_called_with(mock_client)

    async def test_updates_existing_topic(
        self, mock_client: Client, mock_topic_update_transaction: NonCallableMagicMock
    ):
        service = HcsTopicService(mock_client)

        await service.update_topic(
            topic_id=MOCK_TOPIC_ID,
            topic_options=HcsTopicOptions(submit_key=PRIVATE_KEY.public_key(), topic_memo=MOCK_TOPIC_MEMO),
            signing_keys=[PRIVATE_KEY],
        )

        mock_topic_update_transaction.set_memo.assert_called_once()
        mock_topic_update_transaction.set_memo.assert_called_with(MOCK_TOPIC_MEMO)

        mock_topic_update_transaction.sign.assert_called_once()
        mock_topic_update_transaction.sign.assert_called_with(PRIVATE_KEY)

        mock_topic_update_transaction.execute.assert_called_once()
        mock_topic_update_transaction.execute.assert_called_with(mock_client)

    async def test_returns_topic_info(self, mock_client: Client, mock_topic_info_query: NonCallableMagicMock):
        service = HcsTopicService(mock_client)

        topic_info = await service.get_topic_info(MOCK_TOPIC_ID)
        assert topic_info.memo == MOCK_TOPIC_MEMO

        mock_topic_info_query.execute.assert_called_once()
        mock_topic_info_query.execute.assert_called_with(mock_client)
