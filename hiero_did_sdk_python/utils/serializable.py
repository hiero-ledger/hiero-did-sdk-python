import json
from abc import abstractmethod
from typing import Self


class Serializable:
    @classmethod
    def from_json(
        cls,
        json_str: str,
    ) -> Self:
        """Parse a JSON string into an object instance.

        Args:
            json_str: JSON string

        Returns:
            An instance representation of this JSON

        """
        try:
            return cls.from_json_payload(json.loads(json_str))
        except ValueError as e:
            raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure") from e

    @classmethod
    @abstractmethod
    def from_json_payload(cls, payload: dict) -> Self:
        """Create object instance from parsed JSON payload.

        Args:
            payload: parsed JSON dictionary

        Returns:
            Object instance

        """

    def to_json(self) -> str:
        """Create JSON string of object payload.

        Returns:
            A JSON representation of this message

        """
        return json.dumps(self.get_json_payload())

    @abstractmethod
    def get_json_payload(self) -> dict:
        """Get object payload for JSON representation"""
