import time

import pytest

from hiero_did_sdk_python import AnonCredsRevList, AnonCredsRevRegDef, RevRegDefValue
from hiero_did_sdk_python.anoncreds.models.revocation import AnonCredsRevRegEntry, RevRegEntryValue

MOCK_REV_LIST_PARAMS = {
    "issuer_id": "mock-issuer-id",
    "rev_reg_def_id": "mock-rev_reg_def-id",
    "revocation_list": [1, 0, 0, 0, 1],
    "current_accumulator": "mock-accum",
    "timestamp": int(time.time()),
}

MOCK_REV_LIST_JSON_PAYLOAD = {
    "issuerId": MOCK_REV_LIST_PARAMS["issuer_id"],
    "revRegDefId": MOCK_REV_LIST_PARAMS["rev_reg_def_id"],
    "revocationList": MOCK_REV_LIST_PARAMS["revocation_list"],
    "currentAccumulator": MOCK_REV_LIST_PARAMS["current_accumulator"],
    "timestamp": MOCK_REV_LIST_PARAMS["timestamp"],
}

MOCK_REV_REG_DEF = AnonCredsRevRegDef(
    issuer_id="mock-issuer-id",
    cred_def_id="mock-cred-def-id",
    tag="mock-rev-reg-def-tag",
    value=RevRegDefValue(
        public_keys={"accumKey": {"z": "mock-accum-key"}},
        max_cred_num=10,
        tails_location="mock-tails-location",
        tails_hash="mock-tails-hash",
    ),
)

MOCK_REV_ENTRY_1 = AnonCredsRevRegEntry(value=RevRegEntryValue(accum="accum-1", revoked=[5, 9]))
MOCK_REV_ENTRY_2 = AnonCredsRevRegEntry(value=RevRegEntryValue(accum="accum-2", revoked=[8]))
MOCK_REV_ENTRY_3 = AnonCredsRevRegEntry(value=RevRegEntryValue(accum="accum-3", revoked=[0]))


class TestAnonCredsRevList:
    @pytest.mark.parametrize(
        "entries, expected_list, expected_accum",
        [
            ([MOCK_REV_ENTRY_1], [0, 0, 0, 0, 0, 1, 0, 0, 0, 1], "accum-1"),
            ([MOCK_REV_ENTRY_1, MOCK_REV_ENTRY_2], [0, 0, 0, 0, 0, 1, 0, 0, 1, 1], "accum-2"),
            ([MOCK_REV_ENTRY_1, MOCK_REV_ENTRY_3], [1, 0, 0, 0, 0, 1, 0, 0, 0, 1], "accum-3"),
            ([MOCK_REV_ENTRY_1, MOCK_REV_ENTRY_2, MOCK_REV_ENTRY_3], [1, 0, 0, 0, 0, 1, 0, 0, 1, 1], "accum-3"),
        ],
    )
    def test_from_rev_reg_entries(
        self, entries: list[AnonCredsRevRegEntry], expected_list: list[int], expected_accum: str
    ):
        rev_list = AnonCredsRevList.from_rev_reg_entries(
            entries, MOCK_REV_LIST_PARAMS["rev_reg_def_id"], MOCK_REV_REG_DEF
        )
        assert rev_list == AnonCredsRevList(
            revocation_list=expected_list,
            current_accumulator=expected_accum,
            rev_reg_def_id=MOCK_REV_LIST_PARAMS["rev_reg_def_id"],
            issuer_id="mock-issuer-id",
        )

    def test_serializes_to_json(self):
        rev_list = AnonCredsRevList(**MOCK_REV_LIST_PARAMS)
        assert rev_list.get_json_payload() == MOCK_REV_LIST_JSON_PAYLOAD

    def test_deserializes_from_json(self):
        AnonCredsRevList.from_json_payload(MOCK_REV_LIST_JSON_PAYLOAD)

    def test_throws_on_invalid_json(self):
        with pytest.raises(Exception, match=f"{AnonCredsRevList.__name__} JSON parsing failed: Invalid JSON structure"):
            AnonCredsRevList.from_json_payload({})
