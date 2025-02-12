from typing import cast
from unittest.mock import patch

import pytest

from hiero_did_sdk_python.did.did_document_operation import DidDocumentOperation
from hiero_did_sdk_python.did.hcs import HcsDidMessageEnvelope
from hiero_did_sdk_python.did.hcs.events.owner.hcs_did_update_did_owner_event import HcsDidUpdateDidOwnerEvent
from hiero_did_sdk_python.did.hcs.hcs_did_message import HcsDidMessage
from hiero_did_sdk_python.did.hedera_did import HederaDid
from hiero_did_sdk_python.hcs import HcsMessageTransaction

from .common import DID_TOPIC_ID_1, IDENTIFIER


@pytest.fixture
def transaction(mock_client, test_key):
    did = HederaDid(identifier=IDENTIFIER, private_key_der=test_key.private_key.to_string(), client=mock_client)

    message = HcsDidMessage(
        DidDocumentOperation.CREATE,
        IDENTIFIER,
        HcsDidUpdateDidOwnerEvent(
            f"{IDENTIFIER}#did-root-key", cast(str, did.identifier), test_key.public_key, test_key.key_type
        ),
    )

    envelope = HcsDidMessageEnvelope(message)
    envelope.sign(test_key.private_key)

    transaction = HcsMessageTransaction(DID_TOPIC_ID_1, message=envelope)

    return transaction


class TestHcsDidTransaction:
    @patch("hiero_did_sdk_python.hcs.hcs_message_transaction.execute_hcs_transaction_async")
    @pytest.mark.asyncio
    async def test_execute(self, mock_execute_transaction, transaction, mock_client, Something):
        mock_execute_transaction.return_value = {}

        await transaction.execute(mock_client)

        mock_execute_transaction.assert_awaited_once()
        mock_execute_transaction.assert_awaited_with(Something, mock_client)
