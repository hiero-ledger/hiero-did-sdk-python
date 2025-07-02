import asyncio
import time

import pytest
from hiero_sdk_python import Client

from hiero_did_sdk_python import (
    AnonCredsCredDef,
    AnonCredsRevList,
    AnonCredsRevRegDef,
    AnonCredsSchema,
    CredDefValue,
    CredDefValuePrimary,
    HederaAnonCredsRegistry,
    RevRegDefValue,
)
from hiero_did_sdk_python.anoncreds.models.revocation import HcsRevRegEntryMessage, RevRegEntryValue
from hiero_did_sdk_python.anoncreds.types import (
    CredDefState,
    GetCredDefResult,
    GetRevListResult,
    GetRevRegDefResult,
    GetSchemaResult,
    RegisterCredDefResult,
    RegisterRevListResult,
    RegisterRevRegDefResult,
    RegisterSchemaResult,
    RevListState,
    RevRegDefState,
    SchemaState,
)
from hiero_did_sdk_python.anoncreds.utils import AnonCredsObjectType, parse_anoncreds_identifier
from hiero_did_sdk_python.hcs import HcsMessageResolver

from .conftest import NETWORK, OPERATOR_KEY_DER

ISSUER_ID = f"did:hedera:{NETWORK}:zvAQyPeUecGck2EsxcsihxhAB6jZurFrBbj2gC7CNkS5o_0.0.5063027"

MOCK_SCHEMA_PARAMS = {
    "name": "mock-schema",
    "issuer_id": ISSUER_ID,
    "attr_names": ["mock-attr-1", "mock-attr-2"],
    "version": "1",
}

MOCK_CRED_DEF_PARAMS = {
    "schema_id": MOCK_SCHEMA_PARAMS["name"],
    "issuer_id": ISSUER_ID,
    "value": CredDefValue(CredDefValuePrimary(n="n", s="s", r={"key": "value"}, rctxt="rctxt", z="z"), None),
    "tag": "mock-cred-def-tag",
}

MOCK_REV_REG_DEF_PARAMS = {
    "issuer_id": ISSUER_ID,
    "cred_def_id": MOCK_CRED_DEF_PARAMS["tag"],
    "tag": "mock-rev-reg-def-tag",
    "value": RevRegDefValue(
        public_keys={"accumKey": {"z": "mock-accum-key"}},
        max_cred_num=3,
        tails_location="mock-tails-location",
        tails_hash="mock-tails-hash",
    ),
}

REV_LIST_1 = [0, 0, 0]
REV_LIST_2 = [1, 0, 1]

ACCUM_1 = "mock-accum-1"
ACCUM_2 = "mock-accum-2"


# @pytest.mark.flaky(retries=3, delay=1)
@pytest.mark.asyncio(loop_scope="session")
class TestHederaAnonCredsRegistry:
    async def test_creates_anoncreds_schema(self, client: Client, Something):
        registry = HederaAnonCredsRegistry(client)

        schema = AnonCredsSchema(**MOCK_SCHEMA_PARAMS)
        registration_result = await registry.register_schema(schema, OPERATOR_KEY_DER)

        assert registration_result == RegisterSchemaResult(
            schema_state=SchemaState(state="finished", schema=schema, schema_id=Something),
            registration_metadata={},
            schema_metadata={},
        )

        schema_id = registration_result.schema_state.schema_id
        assert schema_id

        parsed_identifier = parse_anoncreds_identifier(schema_id)
        assert parsed_identifier.publisher_did == ISSUER_ID
        assert parsed_identifier.object_type == AnonCredsObjectType.SCHEMA

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(10)

        resolution_result = await registry.get_schema(schema_id)

        assert resolution_result == GetSchemaResult(
            schema=schema, schema_id=schema_id, resolution_metadata={}, schema_metadata={}
        )

    async def test_creates_anoncreds_cred_def(self, client: Client, Something):
        registry = HederaAnonCredsRegistry(client)

        cred_def = AnonCredsCredDef(**MOCK_CRED_DEF_PARAMS)
        registration_result = await registry.register_cred_def(cred_def, OPERATOR_KEY_DER)

        assert registration_result == RegisterCredDefResult(
            credential_definition_state=CredDefState(
                state="finished",
                credential_definition=cred_def,
                credential_definition_id=Something,
            ),
            registration_metadata={},
            credential_definition_metadata={},
        )

        cred_def_id = registration_result.credential_definition_state.credential_definition_id
        assert cred_def_id

        parsed_identifier = parse_anoncreds_identifier(cred_def_id)
        assert parsed_identifier.publisher_did == ISSUER_ID
        assert parsed_identifier.object_type == AnonCredsObjectType.PUBLIC_CRED_DEF

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(10)

        resolution_result = await registry.get_cred_def(cred_def_id)

        assert resolution_result == GetCredDefResult(
            credential_definition=cred_def,
            credential_definition_id=cred_def_id,
            resolution_metadata={},
            credential_definition_metadata={},
        )

    async def test_creates_anoncreds_rev_reg_def(self, client: Client, Something):
        registry = HederaAnonCredsRegistry(client)

        rev_reg_def = AnonCredsRevRegDef(**MOCK_REV_REG_DEF_PARAMS)
        registration_result = await registry.register_rev_reg_def(rev_reg_def, OPERATOR_KEY_DER)

        assert registration_result == RegisterRevRegDefResult(
            revocation_registry_definition_state=RevRegDefState(
                state="finished",
                revocation_registry_definition=rev_reg_def,
                revocation_registry_definition_id=Something,
            ),
            registration_metadata={},
            revocation_registry_definition_metadata={"entriesTopicId": Something},
        )

        rev_reg_def_id = registration_result.revocation_registry_definition_state.revocation_registry_definition_id
        assert rev_reg_def_id

        parsed_identifier = parse_anoncreds_identifier(rev_reg_def_id)
        assert parsed_identifier.publisher_did == ISSUER_ID
        assert parsed_identifier.object_type == AnonCredsObjectType.REV_REG

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(10)

        resolution_result = await registry.get_rev_reg_def(rev_reg_def_id)

        assert resolution_result == GetRevRegDefResult(
            revocation_registry_definition=rev_reg_def,
            revocation_registry_definition_id=rev_reg_def_id,
            resolution_metadata={},
            revocation_registry_definition_metadata={"entriesTopicId": Something},
        )

    async def test_creates_and_updates_rev_list(self, client: Client, Something):
        registry = HederaAnonCredsRegistry(client)

        rev_reg_def = AnonCredsRevRegDef(**MOCK_REV_REG_DEF_PARAMS)
        rev_reg_def_registration_result = await registry.register_rev_reg_def(rev_reg_def, OPERATOR_KEY_DER)

        rev_reg_def_id = (
            rev_reg_def_registration_result.revocation_registry_definition_state.revocation_registry_definition_id
        )
        assert rev_reg_def_id

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(10)

        rev_list = AnonCredsRevList(
            issuer_id=ISSUER_ID,
            revocation_list=REV_LIST_1,
            rev_reg_def_id=rev_reg_def_id,
            current_accumulator=ACCUM_1,
            timestamp=Something,
        )
        rev_list_registration_result = await registry.register_rev_list(rev_list, OPERATOR_KEY_DER)

        assert rev_list_registration_result == RegisterRevListResult(
            revocation_list_state=RevListState(state="finished", revocation_list=rev_list),
            registration_metadata={},
            revocation_list_metadata={},
        )

        rev_reg_entries_topic_id = rev_reg_def_registration_result.revocation_registry_definition_metadata.get(
            "entriesTopicId"
        )
        assert rev_reg_entries_topic_id

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(10)

        entries_messages = await HcsMessageResolver(rev_reg_entries_topic_id, HcsRevRegEntryMessage).execute(client)

        assert len(entries_messages) == 1
        assert entries_messages[0] == HcsRevRegEntryMessage(value=RevRegEntryValue(accum=ACCUM_1))

        rev_list_timestamp = int(time.time())
        rev_list_resolution_result = await registry.get_rev_list(rev_reg_def_id, rev_list_timestamp)

        assert rev_list_resolution_result == GetRevListResult(
            revocation_list=rev_list,
            revocation_registry_id=rev_reg_def_id,
            resolution_metadata={},
            revocation_list_metadata={},
        )

        updated_rev_list = AnonCredsRevList(
            issuer_id=ISSUER_ID,
            revocation_list=REV_LIST_2,
            rev_reg_def_id=rev_reg_def_id,
            current_accumulator=ACCUM_2,
            timestamp=Something,
        )
        rev_list_update_result = await registry.update_rev_list(
            prev_list=rev_list, curr_list=updated_rev_list, revoked=[0, 2], issuer_key_der=OPERATOR_KEY_DER
        )

        assert rev_list_update_result == RegisterRevListResult(
            revocation_list_state=RevListState(state="finished", revocation_list=updated_rev_list),
            registration_metadata={},
            revocation_list_metadata={},
        )

        # Wait until changes are propagated to Hedera Mirror node
        await asyncio.sleep(10)

        entries_messages = await HcsMessageResolver(rev_reg_entries_topic_id, HcsRevRegEntryMessage).execute(client)

        assert len(entries_messages) == 2
        assert entries_messages[0] == HcsRevRegEntryMessage(value=RevRegEntryValue(accum=ACCUM_1))
        assert entries_messages[1] == HcsRevRegEntryMessage(
            value=RevRegEntryValue(accum=ACCUM_2, prev_accum=ACCUM_1, revoked=[0, 2])
        )

        updated_rev_list_resolution_result = await registry.get_rev_list(rev_reg_def_id, int(time.time()))
        assert updated_rev_list_resolution_result == GetRevListResult(
            revocation_list=updated_rev_list,
            revocation_registry_id=rev_reg_def_id,
            resolution_metadata={},
            revocation_list_metadata={},
        )

        rev_list_resolution_result = await registry.get_rev_list(rev_reg_def_id, rev_list_timestamp)
        assert rev_list_resolution_result == GetRevListResult(
            revocation_list=rev_list,
            revocation_registry_id=rev_reg_def_id,
            resolution_metadata={},
            revocation_list_metadata={},
        )
