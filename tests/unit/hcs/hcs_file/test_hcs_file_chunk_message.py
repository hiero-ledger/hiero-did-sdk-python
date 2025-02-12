import pytest

from hiero_did_sdk_python.hcs import HcsFileChunkMessage

MOCK_MESSAGE_PARAMS = {"ordering_index": 0, "chunk_content": "data:application/json;base64,bW9jay1jaHVuay1jb250ZW50"}

MOCK_MESSAGE_JSON_PAYLOAD = {"o": MOCK_MESSAGE_PARAMS["ordering_index"], "c": MOCK_MESSAGE_PARAMS["chunk_content"]}


class TestHcsFileChunkMessage:
    @pytest.mark.parametrize(
        "message_params, expected_validation_result",
        [
            (MOCK_MESSAGE_PARAMS, True),
            ({**MOCK_MESSAGE_PARAMS, "ordering_index": -1}, False),
            ({**MOCK_MESSAGE_PARAMS, "chunk_content": ""}, False),
            ({**MOCK_MESSAGE_PARAMS, "chunk_content": None}, False),
        ],
    )
    def test_validates_content(self, message_params: dict, expected_validation_result: bool):
        valid_message = HcsFileChunkMessage(**message_params)
        assert valid_message.is_valid() == expected_validation_result

    def test_serializes_to_json(self):
        message = HcsFileChunkMessage(**MOCK_MESSAGE_PARAMS)
        assert message.get_json_payload() == MOCK_MESSAGE_JSON_PAYLOAD

    def test_deserializes_from_json(self):
        HcsFileChunkMessage.from_json_payload(MOCK_MESSAGE_JSON_PAYLOAD)

    def test_throws_on_invalid_json(self):
        with pytest.raises(
            Exception, match=f"{HcsFileChunkMessage.__name__} JSON parsing failed: Invalid JSON structure"
        ):
            HcsFileChunkMessage.from_json_payload({})
