from hiero_did_sdk_python.utils.encoding import multibase_decode, multibase_encode

from .common import PRIVATE_KEY


class TestEncoding:
    def test_encoding(self):
        """Test Valid Multibase base58btc with ed25519 pub key encode"""

        public_key_bytes = bytes(PRIVATE_KEY.public_key().to_bytes_raw())
        base58_btc_encoded_string = multibase_encode(public_key_bytes, "base58btc")
        decoded_public_key_bytes = multibase_decode(base58_btc_encoded_string)

        assert base58_btc_encoded_string.startswith("z")
        assert public_key_bytes == decoded_public_key_bytes
