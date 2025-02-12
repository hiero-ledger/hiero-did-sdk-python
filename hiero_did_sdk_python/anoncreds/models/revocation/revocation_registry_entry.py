import json
from dataclasses import dataclass

from zstandard import ZstdCompressor, ZstdDecompressor

from ....hcs import HcsMessage
from ....utils.encoding import b64_to_bytes, bytes_to_b64
from ....utils.serializable import Serializable

DEFAULT_REV_REG_ENTRY_VERSION = "1.0"


@dataclass
class RevRegEntryValue(Serializable):
    """Model representing revocation registry entry value.

    Attributes:
        accum: Current CL accumulator value
        prev_accum: Previous CL accumulator value
        issued: List of issued credential indexes
        revoked: List of revoked credential indexes
    """

    accum: str
    prev_accum: str | None = None
    issued: list[int] | None = None
    revoked: list[int] | None = None

    @classmethod
    def from_json_payload(cls, payload: dict):
        match payload:
            case {"accum": accum, **rest}:
                return cls(
                    accum=accum,
                    prev_accum=rest.get("prevAccum"),
                    issued=rest.get("issued"),
                    revoked=rest.get("revoked"),
                )
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        payload: dict = {"accum": self.accum}

        if self.prev_accum:
            payload["prevAccum"] = self.prev_accum

        if self.issued:
            payload["issued"] = self.issued

        if self.revoked:
            payload["revoked"] = self.revoked

        return payload


@dataclass
class AnonCredsRevRegEntry(Serializable):
    """Model representing AnonCreds revocation registry entry.

    Attributes:
        value: Entry value object
        ver: Entry version
    """

    value: RevRegEntryValue
    ver: str = DEFAULT_REV_REG_ENTRY_VERSION

    @classmethod
    def from_json_payload(cls, payload: dict):
        match payload:
            case {"payload": compressed_str}:
                compressed_bytes = b64_to_bytes(compressed_str)
                entry_params = json.loads(ZstdDecompressor().decompress(compressed_bytes))
                return cls._from_json_payload_raw(entry_params)
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        payload_str = json.dumps(self._get_json_payload_raw()).encode()
        compressed_payload = ZstdCompressor().compress(payload_str)
        return {"payload": bytes_to_b64(compressed_payload)}

    @classmethod
    def _from_json_payload_raw(cls, payload: dict):
        match payload:
            case {"ver": ver, "value": value}:
                return cls(ver=ver, value=RevRegEntryValue.from_json_payload(value))
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def _get_json_payload_raw(self):
        return {"ver": self.ver, "value": self.value.get_json_payload()}


class HcsRevRegEntryMessage(HcsMessage, AnonCredsRevRegEntry):
    """HCS message class for submitting revocation registry entries."""

    def is_valid(self, topic_id: str | None = None) -> bool:
        return bool(self.value) and bool(self.value.accum)
