import base64
from abc import ABC, abstractmethod
from enum import Enum
from typing import ClassVar, Literal

import base58


class MultibaseEncoder(ABC):
    """Encoding details."""

    name: ClassVar[str]
    prefix: ClassVar[str]

    @abstractmethod
    def encode(self, value: bytes) -> str:
        """Encode a byte string using this encoding."""

    @abstractmethod
    def decode(self, value: str) -> bytes:
        """Decode a string using this encoding."""


class Base58BtcEncoder(MultibaseEncoder):
    """Base58BTC encoding."""

    name = "base58btc"
    prefix = "z"

    def encode(self, value: bytes) -> str:
        """Encode a byte string using the base58btc encoding."""
        return base58.b58encode(value).decode()

    def decode(self, value: str) -> bytes:
        """Decode a multibase encoded string."""
        return base58.b58decode(value)


class Encoding(Enum):
    """Enum for supported encodings."""

    base58btc = Base58BtcEncoder()
    # Insert additional encodings here

    @classmethod
    def from_name(cls, name: str) -> MultibaseEncoder:
        """Get encoding from name."""
        for encoding in cls:
            if encoding.value.name == name:
                return encoding.value
        raise ValueError(f"Unsupported encoding: {name}")

    @classmethod
    def from_prefix(cls, character: str) -> MultibaseEncoder:
        """Get encoding from character."""
        for encoding in cls:
            if encoding.value.prefix == character:
                return encoding.value
        raise ValueError(f"Unsupported encoding: {character}")


EncodingStr = Literal[
    "base58btc",
    # Insert additional encoding names here
]


def multibase_encode(value: bytes, encoding: Encoding | EncodingStr) -> str:
    """Encode a byte string using the given encoding.

    Args:
        value: The byte string to encode
        encoding: The encoding to use

    Returns:
        The encoded string
    """
    if isinstance(encoding, str):
        encoder = Encoding.from_name(encoding)
    elif isinstance(encoding, Encoding):
        encoder = encoding.value
    else:
        raise TypeError("encoding must be an Encoding or EncodingStr")

    return encoder.prefix + encoder.encode(value)


def multibase_decode(value: str) -> bytes:
    """Decode a multibase encoded string.

    Args:
        value: The string to decode

    Returns:
        The decoded byte string
    """
    encoding = value[0]
    encoded = value[1:]
    encoder = Encoding.from_prefix(encoding)

    return encoder.decode(encoded)


def pad(val: str) -> str:
    """Pad base64 values if needed."""
    padlen = 4 - len(val) % 4
    return val if padlen > 2 else (val + "=" * padlen)


def unpad(val: str) -> str:
    """Remove padding from base64 values if needed."""
    return val.rstrip("=")


def b64_to_bytes(val: str, urlsafe=False) -> bytes:
    """Convert a base 64 string to bytes."""
    if urlsafe:
        return base64.urlsafe_b64decode(pad(val))
    return base64.b64decode(pad(val))


def b64_to_str(val: str, urlsafe=False, encoding=None) -> str:
    """Convert a base 64 string to string on input encoding (default utf-8)."""
    return b64_to_bytes(val, urlsafe).decode(encoding or "utf-8")


def bytes_to_b64(val: bytes, urlsafe=False, pad=True, encoding: str = "ascii") -> str:
    """Convert a byte string to base 64."""
    b64 = base64.urlsafe_b64encode(val).decode(encoding) if urlsafe else base64.b64encode(val).decode(encoding)
    return b64 if pad else unpad(b64)


def str_to_b64(val: str, urlsafe=False, encoding=None, pad=True) -> str:
    """Convert a string to base64 string on input encoding (default utf-8)."""
    return bytes_to_b64(val.encode(encoding or "utf-8"), urlsafe, pad)


def is_b64(val: str) -> bool:
    try:
        base64.b64decode(pad(unpad(val)), validate=True)
        return True
    except Exception:
        return False


def b58_to_bytes(val: str) -> bytes:
    """Convert a base 58 string to bytes."""
    return base58.b58decode(val)


def bytes_to_b58(val: bytes, encoding=None) -> str:
    """Convert a byte string to base 58."""
    return base58.b58encode(val).decode(encoding or "utf-8")
