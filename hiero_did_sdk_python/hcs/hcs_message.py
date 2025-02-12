from abc import ABC, abstractmethod
from dataclasses import dataclass
from hashlib import sha256

from hiero_sdk_python import Timestamp

from ..utils.serializable import Serializable


class HcsMessage(ABC, Serializable):
    """Base class for HCS messages"""

    @abstractmethod
    def is_valid(self, topic_id: str | None = None) -> bool:
        """Validate the message against specific HCS topic"""

    def get_payload_hash(self) -> str:
        return sha256(self.to_json().encode()).hexdigest()


@dataclass
class HcsMessageWithResponseMetadata:
    message: HcsMessage
    consensus_timestamp: Timestamp
    sequence_number: float

    def get_payload_hash(self) -> str:
        return self.message.get_payload_hash()
