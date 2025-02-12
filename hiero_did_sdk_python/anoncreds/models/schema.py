from dataclasses import dataclass

from ...utils.serializable import Serializable


@dataclass
class AnonCredsSchema(Serializable):
    """Model representing AnonCreds schema.

    Attributes:
        name: Schema name
        issuer_id: Schema issuer DID
        attr_names: List of schema attribute names
        version: Schema version
    """

    name: str
    issuer_id: str
    attr_names: list[str]
    version: str

    @classmethod
    def from_json_payload(cls, payload: dict):
        match payload:
            case {"name": name, "issuerId": issuer_id, "attrNames": attr_names, "version": version}:
                return cls(name=name, issuer_id=issuer_id, attr_names=attr_names, version=version)
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        return {"name": self.name, "issuerId": self.issuer_id, "attrNames": self.attr_names, "version": self.version}
