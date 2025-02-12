from hiero_sdk_python import PrivateKey, PublicKey

from ..did.types import SupportedKeyType


def get_key_type(key: PrivateKey | PublicKey) -> SupportedKeyType:
    if key.is_ed25519():
        return "Ed25519VerificationKey2018"
    elif key.is_ecdsa():
        return "EcdsaSecp256k1VerificationKey2019"
    else:
        raise Exception("Unknown key type")
