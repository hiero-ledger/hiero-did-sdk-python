import pytest
from hiero_sdk_python import Client

from hiero_did_sdk_python.hcs import HcsTopicOptions, HcsTopicService

from .conftest import OPERATOR_KEY


# @pytest.mark.flaky(retries=3, delay=1)
@pytest.mark.asyncio(loop_scope="session")
class TestHcsTopicService:
    async def test_creates_and_updates_hcs_topic(self, client: Client):
        service = HcsTopicService(client)

        topic_id = await service.create_topic(
            topic_options=HcsTopicOptions(
                submit_key=OPERATOR_KEY.public_key(), admin_key=OPERATOR_KEY.public_key(), topic_memo="topic_memo"
            ),
            signing_keys=[OPERATOR_KEY],
        )

        topic_info = await service.get_topic_info(topic_id)
        assert topic_info.memo == "topic_memo"

        await service.update_topic(
            topic_id,
            HcsTopicOptions(submit_key=OPERATOR_KEY.public_key(), topic_memo="updated-topic-memo"),
            signing_keys=[OPERATOR_KEY],
        )

        topic_info = await service.get_topic_info(topic_id)
        assert topic_info.memo == "updated-topic-memo"

    async def test_creates_immutable_topic_without_admin_key(self, client: Client):
        service = HcsTopicService(client)

        topic_id = await service.create_topic(
            topic_options=HcsTopicOptions(submit_key=OPERATOR_KEY.public_key(), topic_memo="topic_memo"),
            signing_keys=[OPERATOR_KEY],
        )

        with pytest.raises(Exception, match="Error retrieving transaction receipt: UNAUTHORIZED"):
            await service.update_topic(
                topic_id,
                HcsTopicOptions(submit_key=OPERATOR_KEY.public_key(), topic_memo="updated-topic-memo"),
                signing_keys=[OPERATOR_KEY],
            )
