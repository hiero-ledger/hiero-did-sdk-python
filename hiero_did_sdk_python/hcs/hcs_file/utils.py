from zstandard import ZstdCompressor, ZstdDecompressor

from ...utils.encoding import b64_to_bytes, bytes_to_b64
from ..constants import BASE64_JSON_CONTENT_PREFIX
from .hcs_file_chunk_message import HcsFileChunkMessage


def get_file_chunk_messages(payload: bytes) -> list[HcsFileChunkMessage]:
    try:
        compressed_payload = ZstdCompressor().compress(payload)
        message_content = f"{BASE64_JSON_CONTENT_PREFIX}{bytes_to_b64(compressed_payload)}".encode()

        result: list[HcsFileChunkMessage] = []

        for chunk_index, range_index in enumerate(
            range(0, len(message_content), HcsFileChunkMessage.MAX_CHUNK_CONTENT_SIZE_IN_BYTES)
        ):
            chunk_content = message_content[
                range_index : range_index + HcsFileChunkMessage.MAX_CHUNK_CONTENT_SIZE_IN_BYTES
            ]
            result.append(HcsFileChunkMessage(ordering_index=chunk_index, chunk_content=chunk_content.decode()))

        return result
    except Exception as error:
        raise Exception(f"Error on getting chunk messages for HCS-1 file: {error!s}") from error


def build_file_from_chunk_messages(chunk_messages: list[HcsFileChunkMessage]) -> bytes:
    message_content: str = ""

    try:
        for chunk_message in sorted(chunk_messages, key=lambda message: message.ordering_index):
            message_content += chunk_message.content

        compressed_payload = b64_to_bytes(message_content.removeprefix(BASE64_JSON_CONTENT_PREFIX))
        return ZstdDecompressor().decompress(compressed_payload)
    except Exception as error:
        raise Exception(f"Error on building HCS-1 file payload from chunk messages: {error!s}") from error
