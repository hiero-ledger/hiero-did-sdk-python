from dataclasses import dataclass
from typing import ClassVar

from ...utils.serializable import Serializable

CREDENTIAL_DEFINITION_TYPE = "CL"


@dataclass
class CredDefValuePrimary(Serializable):
    """Model of primary credential definition value.

    Args:
        n: Safe RSA-2048 number
        s: Randomly selected quadratic residue of n
        r: Object that defines a CL-RSA public key fragment for each attribute in the credential
        rctxt: Equal to s^(xrctxt), where xrctxt is a randomly selected integer between 2 and p'q'-1
        z: is equal to s^(xz), where xz is a randomly selected integer between 2
            and p'q'-1. This makes up part of the CL-RSA public key, independent of
            the message blocks being signed
    """

    n: str
    s: str
    r: dict
    rctxt: str
    z: str

    @classmethod
    def from_json_payload(cls, payload: dict):
        match payload:
            case {"n": n, "s": s, "r": r, "rctxt": rctxt, "z": z}:
                return cls(n, s, r, rctxt, z)
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return self.__dict__


@dataclass
class CredDefValueRevocation(Serializable):
    """Model of revocation-specific credential definition value.

    Args:
        g: Generator for the elliptic curve group G1
        g_dash: Generator for the elliptic curve group G2
        h: Elliptic curve point selected uniformly at random from G1
        h0: Elliptic curve point selected uniformly at random from G1
        h1: Elliptic curve point selected uniformly at random from G1
        h2: Elliptic curve point selected uniformly at random from G1
        htilde: Elliptic curve point selected uniformly at random from G1
        h_cap: Elliptic curve point selected uniformly at random from G2
        u: Elliptic curve point selected uniformly at random from G2
        pk: Public key in G1 for the issuer with respect to this accumulator, computed as g^sk (in multiplicative notation), where sk is from r_key above
        y: Elliptic curve point in G2. computed as h_cap^x (in multiplicative notation), where x is from r_key above
    """

    g: str
    g_dash: str
    h: str
    h0: str
    h1: str
    h2: str
    htilde: str
    h_cap: str
    u: str
    pk: str
    y: str

    @classmethod
    def from_json_payload(cls, payload: dict):
        match payload:
            case {
                "g": g,
                "g_dash": g_dash,
                "h": h,
                "h0": h0,
                "h1": h1,
                "h2": h2,
                "htilde": htilde,
                "h_cap": h_cap,
                "u": u,
                "pk": pk,
                "y": y,
            }:
                return cls(g, g_dash, h, h0, h1, h2, htilde, h_cap, u, pk, y)
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return self.__dict__


@dataclass
class CredDefValue(Serializable):
    """Model representing AnonCreds credential definition value.

    Attributes:
        primary: Credential definition primary value
        revocation: Credential definition revocation-specific value
    """

    primary: CredDefValuePrimary
    revocation: CredDefValueRevocation | None

    @classmethod
    def from_json_payload(cls, payload: dict):
        match payload:
            case {"primary": primary, "revocation": revocation}:
                return cls(
                    CredDefValuePrimary.from_json_payload(primary), CredDefValueRevocation.from_json_payload(revocation)
                )
            case {"primary": primary}:
                return cls(CredDefValuePrimary.from_json_payload(primary), None)
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        payload = {"primary": self.primary.get_json_payload()}

        if self.revocation:
            payload["revocation"] = self.revocation.get_json_payload()

        return payload


@dataclass
class AnonCredsCredDef(Serializable):
    """Model representing AnonCreds credential definition.

    Attributes:
        issuer_id: Credential definition issuer DID
        schema_id: Schema ID
        type_: Credential definition type. Only "CL" type is currently supported
        tag: Credential definition tag
        value: Definition value object
    """

    issuer_id: str
    schema_id: str
    type_: ClassVar[str] = CREDENTIAL_DEFINITION_TYPE
    tag: str
    value: CredDefValue

    @classmethod
    def from_json_payload(cls, payload: dict):
        match payload:
            case {"issuerId": issuer_id, "schemaId": schema_id, "type": type_, "tag": tag, "value": value}:
                if type_ != CREDENTIAL_DEFINITION_TYPE:
                    raise Exception(f"Unsupported Anoncreds Cred Def type: {type_}")
                return cls(
                    issuer_id=issuer_id, schema_id=schema_id, tag=tag, value=CredDefValue.from_json_payload(value)
                )
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return {
            "issuerId": self.issuer_id,
            "schemaId": self.schema_id,
            "type": self.type_,
            "tag": self.tag,
            "value": self.value.get_json_payload(),
        }
