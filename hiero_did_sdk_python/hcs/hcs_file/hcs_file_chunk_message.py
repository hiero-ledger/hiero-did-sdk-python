from typing import ClassVar

from ..hcs_message import HcsMessage


class HcsFileChunkMessage(HcsMessage):
    # 1024 bytes is a max size for HCS transaction (non-chunked) + we're reserving some space for JSON structural characters - 64 bytes
    MAX_CHUNK_CONTENT_SIZE_IN_BYTES: ClassVar[int] = 960

    def __init__(self, ordering_index: int, chunk_content: str):
        self.ordering_index = ordering_index
        self.content = chunk_content

    def is_valid(self, topic_id: str | None = None) -> bool:
        return bool(self.ordering_index is not None and self.ordering_index >= 0 and self.content)

    @classmethod
    def from_json_payload(cls, payload: dict):
        match payload:
            case {"o": ordering_index, "c": content}:
                return cls(ordering_index=ordering_index, chunk_content=content)
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return {"o": self.ordering_index, "c": self.content}
