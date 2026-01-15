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
        "test_file_path, expected_chunks_count, expected_hash",
        [
            ("./tests/test_data/test_file.txt", 1, "48457c7f847ac24fc2419106eae4bb62cf90e25cfb4de0e334fb57df4f7aa4c4"),
            (
                "./tests/test_data/test_file_large.txt",
                6,
                "96ec5e6330a0850610a81b24b103b1b61ccf38884f5453427229c27e818f42ef",
            ),
        ],
    )
    async def test_submit_and_resolve_file(
        self, test_file_path: str, expected_chunks_count: int, expected_hash: str, client: Client
    ):
        service = HcsFileService(client)
        file_payload = Path(test_file_path).read_bytes()

        topic_id = await service.submit_file(file_payload, OPERATOR_KEY_DER)

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(5)

        topic_info = await execute_hcs_query_async(TopicInfoQuery(topic_id=TopicId.from_string(topic_id)), client)
        topic_messages = await HcsMessageResolver(topic_id, HcsFileChunkMessage).execute(client)

        assert topic_info.memo == f"{sha256(file_payload).hexdigest()}:zstd:base64"
        assert len(topic_messages) == expected_chunks_count

        resolved_payload = await service.resolve_file(topic_id)
        assert resolved_payload

        topic_file_hash, _, _ = topic_info.memo.split(":")

        assert topic_file_hash == sha256(resolved_payload).hexdigest()
        assert topic_file_hash == expected_hash
