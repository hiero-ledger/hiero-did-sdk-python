from dataclasses import dataclass

from ....utils.serializable import Serializable
from .revocation_registry_definition import AnonCredsRevRegDef
from .revocation_registry_entry import AnonCredsRevRegEntry


def _indexes_to_bit_array(indexes: list[int], size: int) -> list[int]:
    """Turn a sequence of indexes into a full state bit array."""
    return [1 if index in indexes else 0 for index in range(0, size)]


@dataclass
class AnonCredsRevList(Serializable):
    """Model representing AnonCreds revocation list object.

    Attributes:
        issuer_id: Revocation registry issuer DID
        rev_reg_def_id: Revocation registry definition ID
        revocation_list: Revocation list that represents state (revoked/non-revoked) of each credential in registry, list size correspond to number of credentials that revocation registry can hold
        current_accumulator: Current value of CL accumulator
        timestamp: Timestamp associated with revocation list instance
    """

    issuer_id: str
    rev_reg_def_id: str
    revocation_list: list[int]
    current_accumulator: str
    timestamp: int | None = None

    @classmethod
    def from_rev_reg_entries(
        cls,
        entries: list[AnonCredsRevRegEntry],
        rev_reg_id: str,
        rev_reg_def: AnonCredsRevRegDef,
        timestamp: int | None = None,
    ):
        """Build revocation list object from corresponding revocation registry entries.

        Args:
            entries: List of revocation registry entries to build state from
            rev_reg_id: Revocation registry ID
            rev_reg_def: Revocation registry definition object
            timestamp: Requested timestamp to associate revocation list with
        """
        revoked_indexes = []

        for entry in entries:
            if entry.value.revoked:
                revoked_indexes += entry.value.revoked

        rev_list_bit_array = _indexes_to_bit_array(revoked_indexes, rev_reg_def.value.max_cred_num)
        accum = entries[-1].value.accum

        return cls(
            issuer_id=rev_reg_def.issuer_id,
            rev_reg_def_id=rev_reg_id,
            revocation_list=rev_list_bit_array,
            current_accumulator=accum,
            timestamp=timestamp,
        )

    @classmethod
    def from_json_payload(cls, payload: dict):
        match payload:
            case {
                "issuerId": issuer_id,
                "revRegDefId": rev_reg_def_id,
                "revocationList": revocation_list,
                "currentAccumulator": current_accumulator,
                **rest,
            }:
                return cls(
                    issuer_id=issuer_id,
                    rev_reg_def_id=rev_reg_def_id,
                    revocation_list=revocation_list,
                    current_accumulator=current_accumulator,
                    timestamp=rest.get("timestamp"),
                )
            case _:
                raise Exception(f"{cls.__name__} JSON parsing failed: Invalid JSON structure")

    def get_json_payload(self):
        payload = {
            "issuerId": self.issuer_id,
            "revRegDefId": self.rev_reg_def_id,
            "revocationList": self.revocation_list,
            "currentAccumulator": self.current_accumulator,
        }

        if self.timestamp:
            payload["timestamp"] = self.timestamp

        return payload
