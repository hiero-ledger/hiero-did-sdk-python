from dataclasses import dataclass
from typing import ClassVar, TypedDict

from ....utils.serializable import Serializable

REVOCATION_REGISTRY_TYPE = "CL_ACCUM"


@dataclass
class RevRegDefValue(Serializable):
    """Model representing revocation registry definition value.

    Attributes:
        public_keys: Revocation registry public keys
        max_cred_num: Max number of credentials which revocation state can be tracked in the registry
        tails_location: Registry tails file location
        tails_hash: Registry tails file hash
    """

    public_keys: dict
    max_cred_num: int
    tails_location: str
    tails_hash: str

    @classmethod
    def from_json_payload(cls, payload: dict):
        match payload:
            case {
                "publicKeys": public_keys,
                "maxCredNum": max_cred_num,
                "tailsLocation": tails_location,
                "tailsHash": tails_hash,
            }:
                return cls(public_keys, max_cred_num, tails_location, tails_hash)
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return {
            "publicKeys": self.public_keys,
            "maxCredNum": self.max_cred_num,
            "tailsLocation": self.tails_location,
            "tailsHash": self.tails_hash,
        }


@dataclass
class AnonCredsRevRegDef(Serializable):
    """Model representing AnonCreds revocation registry definition.

    Attributes:
        issuer_id: Revocation registry issuer DID
        type_: Revocation registry type. Only "CL_ACCUM" type is currently supported
        cred_def_id: Credential definition ID
        tag: Revocation registry tag
        value: Definition value object
    """

    issuer_id: str
    type_: ClassVar[str] = REVOCATION_REGISTRY_TYPE
    cred_def_id: str
    tag: str
    value: RevRegDefValue

    @classmethod
    def from_json_payload(cls, payload: dict):
        match payload:
            case {"issuerId": issuer_id, "type": type_, "credDefId": cred_def_id, "tag": tag, "value": value}:
                if type_ != REVOCATION_REGISTRY_TYPE:
                    raise Exception(f"Unsupported Anoncreds Revocation Registry type: {type_}")
                return cls(
                    issuer_id=issuer_id, cred_def_id=cred_def_id, tag=tag, value=RevRegDefValue.from_json_payload(value)
                )
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return {
            "issuerId": self.issuer_id,
            "type": self.type_,
            "credDefId": self.cred_def_id,
            "tag": self.tag,
            "value": self.value.get_json_payload(),
        }


class RevRegDefHcsMetadata(TypedDict):
    entries_topic_id: str


@dataclass(frozen=True)
class RevRegDefWithHcsMetadata(Serializable):
    """HCS specific model used to publish registry definition model along with HCS metadata."""

    rev_reg_def: AnonCredsRevRegDef
    hcs_metadata: RevRegDefHcsMetadata

    @classmethod
    def from_json_payload(cls, payload: dict):
        match payload:
            case {"revRegDef": rev_reg_def, "hcsMetadata": hcs_metadata}:
                return cls(rev_reg_def=AnonCredsRevRegDef.from_json_payload(rev_reg_def), hcs_metadata=hcs_metadata)
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return {
            "revRegDef": self.rev_reg_def.get_json_payload(),
            "hcsMetadata": self.hcs_metadata,
        }
