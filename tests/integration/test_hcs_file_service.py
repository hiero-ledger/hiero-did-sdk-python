import asyncio
from hashlib import sha256
from pathlib import Path

import pytest
from hiero_sdk_python import Client, TopicId, TopicInfoQuery

from hiero_did_sdk_python.hcs import HcsFileChunkMessage, HcsFileService, HcsMessageResolver, execute_hcs_query_async

from .conftest import OPERATOR_KEY_DER


@pytest.mark.flaky(retries=3, delay=1)
@pytest.mark.asyncio(loop_scope="session")
class TestHcsFileService:
    @pytest.mark.parametrize(
        "test_file_path, expected_chunks_count",
        [("./tests/test_data/test_file.txt", 1), ("./tests/test_data/test_file_large.txt", 6)],
    )
    async def test_submit_file(self, test_file_path: str, expected_chunks_count: int, client: Client):
        service = HcsFileService(client)
        file_payload = Path(test_file_path).read_bytes()

        topic_id = await service.submit_file(file_payload, OPERATOR_KEY_DER)

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(5)

        topic_info = await execute_hcs_query_async(TopicInfoQuery(topic_id=TopicId.from_string(topic_id)), client)
        topic_messages = await HcsMessageResolver(topic_id, HcsFileChunkMessage).execute(client)

        assert topic_info.memo == f"{sha256(file_payload).hexdigest()}:zstd:base64"
        assert len(topic_messages) == expected_chunks_count

    @pytest.mark.parametrize(
        "topic_id, expected_hash",
        [
            ("0.0.5123926", "ea4d17b8c0cf44c215ade6b4ad36832672ea3188b1dad12b68c2472dfbcdeff1"),
            ("0.0.5123993", "dce9e97491cb7bbaeb6f1af9c236a62f5b6f3f4c07952b5431daa52ec58fbc0b"),
        ],
    )
    async def test_resolve_file(self, topic_id: str, expected_hash: str, client: Client):
        service = HcsFileService(client)

        resolved_payload = await service.resolve_file(topic_id)
        assert resolved_payload

        topic_info = await execute_hcs_query_async(TopicInfoQuery(topic_id=TopicId.from_string(topic_id)), client)
        topic_file_hash, _, _ = topic_info.memo.split(":")

        assert topic_file_hash == sha256(resolved_payload).hexdigest()
        assert topic_file_hash == expected_hash
