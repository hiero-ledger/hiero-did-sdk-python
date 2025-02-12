import time
from unittest.mock import NonCallableMagicMock, call

import pytest
from hiero_sdk_python import Client, Timestamp
from pytest_mock import MockerFixture

from hiero_did_sdk_python import (
    AnonCredsCredDef,
    AnonCredsRevList,
    AnonCredsRevRegDef,
    AnonCredsSchema,
    CredDefValue,
    CredDefValuePrimary,
    HederaAnonCredsRegistry,
    MemoryCache,
    RevRegDefValue,
)
from hiero_did_sdk_python.anoncreds.models.revocation import (
    HcsRevRegEntryMessage,
    RevRegDefWithHcsMetadata,
    RevRegEntryValue,
)
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
from hiero_did_sdk_python.anoncreds.utils import AnonCredsObjectType, build_anoncreds_identifier
from hiero_did_sdk_python.hcs import (
    HcsFileService,
    HcsMessageResolver,
    HcsMessageTransaction,
    HcsMessageWithResponseMetadata,
    HcsTopicService,
)
from tests.integration.conftest import OPERATOR_KEY_DER

ISSUER_ID = "did:hedera:testnet:zvAQyPeUecGck2EsxcsihxhAB6jZurFrBbj2gC7CNkS5o_0.0.5063027"

MOCK_SCHEMA_TOPIC_ID = "0.0.5063030"
MOCK_SCHEMA_ID = build_anoncreds_identifier(
    publisher_did=ISSUER_ID, topic_id=MOCK_SCHEMA_TOPIC_ID, object_type=AnonCredsObjectType.SCHEMA
)
MOCK_SCHEMA = AnonCredsSchema(
    name="mock-schema",
    issuer_id=ISSUER_ID,
    attr_names=["mock-attr-1", "mock-attr-2"],
    version="1.0.0",
)

MOCK_CRED_DEF_TOPIC_ID = "0.0.5063040"
MOCK_CRED_DEF_ID = build_anoncreds_identifier(
    publisher_did=ISSUER_ID, topic_id=MOCK_CRED_DEF_TOPIC_ID, object_type=AnonCredsObjectType.PUBLIC_CRED_DEF
)
MOCK_CRED_DEF = AnonCredsCredDef(
    schema_id=MOCK_SCHEMA_ID,
    issuer_id=ISSUER_ID,
    tag="mock-cred-def-tag",
    value=CredDefValue(CredDefValuePrimary(n="n", s="s", r={"key": "value"}, rctxt="rctxt", z="z"), None),
)

MOCK_REV_REG_DEF_TOPIC_ID = "0.0.5063050"
MOCK_REV_REG_DEF_ID = build_anoncreds_identifier(
    publisher_did=ISSUER_ID, topic_id=MOCK_REV_REG_DEF_TOPIC_ID, object_type=AnonCredsObjectType.REV_REG
)
MOCK_REV_REG_DEF = AnonCredsRevRegDef(
    issuer_id=ISSUER_ID,
    cred_def_id=MOCK_CRED_DEF_ID,
    tag="mock-rev-reg-def-tag",
    value=RevRegDefValue(
        public_keys={"accumKey": {"z": "mock-accum-key"}},
        max_cred_num=15,
        tails_location="mock-tails-location",
        tails_hash="mock-tails-hash",
    ),
)

MOCK_REV_REG_ENTRIES_TOPIC_ID = "0.0.5063060"
MOCK_REV_REG_DEF_WITH_METADATA = RevRegDefWithHcsMetadata(
    rev_reg_def=MOCK_REV_REG_DEF, hcs_metadata={"entries_topic_id": MOCK_REV_REG_ENTRIES_TOPIC_ID}
)

MOCK_REV_ENTRY_1 = HcsRevRegEntryMessage(value=RevRegEntryValue(accum="accum-1", revoked=[5, 10]))
MOCK_REV_ENTRY_2 = HcsRevRegEntryMessage(value=RevRegEntryValue(accum="accum-2", revoked=[12]))
MOCK_REV_ENTRY_3 = HcsRevRegEntryMessage(value=RevRegEntryValue(accum="accum-3", revoked=[0]))

MOCK_REV_ENTRY_MESSAGES_WITH_METADATA = [
    HcsMessageWithResponseMetadata(
        message=MOCK_REV_ENTRY_1, consensus_timestamp=Timestamp(seconds=100, nanos=0), sequence_number=1
    ),
    HcsMessageWithResponseMetadata(
        message=MOCK_REV_ENTRY_2, consensus_timestamp=Timestamp(seconds=200, nanos=0), sequence_number=2
    ),
    HcsMessageWithResponseMetadata(
        message=MOCK_REV_ENTRY_3, consensus_timestamp=Timestamp(seconds=300, nanos=0), sequence_number=3
    ),
]


@pytest.fixture(scope="session")
def mock_rev_list(Something):
    return AnonCredsRevList.from_rev_reg_entries(
        entries=[MOCK_REV_ENTRY_1, MOCK_REV_ENTRY_2, MOCK_REV_ENTRY_3],
        rev_reg_id=MOCK_REV_REG_DEF_ID,
        rev_reg_def=MOCK_REV_REG_DEF,
        timestamp=Something,
    )


@pytest.fixture(scope="session")
def mock_rev_list_previous(Something):
    return AnonCredsRevList.from_rev_reg_entries(
        entries=[MOCK_REV_ENTRY_1, MOCK_REV_ENTRY_2],
        rev_reg_id=MOCK_REV_REG_DEF_ID,
        rev_reg_def=MOCK_REV_REG_DEF,
        timestamp=Something,
    )


@pytest.fixture
def mock_hcs_file_service(mocker: MockerFixture):
    MockHcsFileService = mocker.patch(
        "hiero_did_sdk_python.anoncreds.hedera_anoncreds_registry.HcsFileService", autospec=HcsFileService
    )

    mock_hcs_file_service = MockHcsFileService.return_value
    mock_hcs_file_service.resolve_file = mocker.AsyncMock()
    mock_hcs_file_service.submit_file = mocker.AsyncMock()

    return mock_hcs_file_service


@pytest.fixture
def mock_hcs_topic_service(mocker: MockerFixture):
    MockHcsTopicService = mocker.patch(
        "hiero_did_sdk_python.anoncreds.hedera_anoncreds_registry.HcsTopicService", autospec=HcsTopicService
    )

    mock_hsc_topic_service = MockHcsTopicService.return_value
    mock_hsc_topic_service.create_topic.return_value = MOCK_REV_REG_DEF_WITH_METADATA.hcs_metadata["entries_topic_id"]

    return mock_hsc_topic_service


@pytest.fixture
def mock_hcs_message_transaction(mocker: MockerFixture):
    MockHcsMessageTransaction = mocker.patch(
        "hiero_did_sdk_python.anoncreds.hedera_anoncreds_registry.HcsMessageTransaction", autospec=HcsMessageTransaction
    )

    mock_hcs_message_transaction = MockHcsMessageTransaction.return_value
    mock_hcs_message_transaction.execute = mocker.AsyncMock()

    return mock_hcs_message_transaction


@pytest.fixture
def mock_hcs_message_resolver(mocker: MockerFixture):
    MockHcsMessageResolver = mocker.patch(
        "hiero_did_sdk_python.anoncreds.hedera_anoncreds_registry.HcsMessageResolver", autospec=HcsMessageResolver
    )

    mock_hcs_message_resolver = MockHcsMessageResolver.return_value
    mock_hcs_message_resolver.execute.return_value = MOCK_REV_ENTRY_MESSAGES_WITH_METADATA

    return mock_hcs_message_resolver


@pytest.mark.asyncio(loop_scope="session")
class TestHederaAnonCredsRegistry:
    class TestSchema:
        async def test_resolves_schema_hcs_file(self, mock_client: Client, mock_hcs_file_service: NonCallableMagicMock):
            mock_hcs_file_service.resolve_file.return_value = MOCK_SCHEMA.to_json().encode()

            registry = HederaAnonCredsRegistry(mock_client)
            schema_resolution_result = await registry.get_schema(MOCK_SCHEMA_ID)

            assert schema_resolution_result == GetSchemaResult(
                schema=MOCK_SCHEMA,
                schema_id=MOCK_SCHEMA_ID,
                resolution_metadata={},
                schema_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_SCHEMA_TOPIC_ID)

        async def test_resolve_returns_not_found(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
        ):
            mock_hcs_file_service.resolve_file.return_value = None

            registry = HederaAnonCredsRegistry(mock_client)
            schema_resolution_result = await registry.get_schema(MOCK_SCHEMA_ID)

            assert schema_resolution_result == GetSchemaResult(
                schema_id=MOCK_SCHEMA_ID,
                resolution_metadata={
                    "error": "notFound",
                    "message": f"AnonCreds schema with id '{MOCK_SCHEMA_ID}' not found",
                },
                schema_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_SCHEMA_TOPIC_ID)

        async def test_resolve_returns_not_found_on_invalid_id(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
        ):
            registry = HederaAnonCredsRegistry(mock_client)
            schema_resolution_result = await registry.get_schema(MOCK_CRED_DEF_ID)

            assert schema_resolution_result == GetSchemaResult(
                schema_id=MOCK_CRED_DEF_ID,
                resolution_metadata={
                    "error": "notFound",
                    "message": f"AnonCreds Schema id '{MOCK_CRED_DEF_ID}' is invalid",
                },
                schema_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_not_awaited()

        async def test_registers_schema_as_hcs_file(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
        ):
            mock_hcs_file_service.submit_file.return_value = MOCK_SCHEMA_TOPIC_ID

            registry = HederaAnonCredsRegistry(mock_client)
            schema_register_result = await registry.register_schema(MOCK_SCHEMA, OPERATOR_KEY_DER)

            assert schema_register_result == RegisterSchemaResult(
                schema_state=SchemaState(
                    state="finished",
                    schema=MOCK_SCHEMA,
                    schema_id=build_anoncreds_identifier(ISSUER_ID, MOCK_SCHEMA_TOPIC_ID, AnonCredsObjectType.SCHEMA),
                ),
                schema_metadata={},
                registration_metadata={},
            )

            mock_hcs_file_service.submit_file.assert_awaited_once()
            mock_hcs_file_service.submit_file.assert_awaited_with(MOCK_SCHEMA.to_json().encode(), OPERATOR_KEY_DER)

        async def test_resolve_hits_cache(self, mock_client: Client, mocker: MockerFixture):
            mock_cache_get = mocker.patch("hiero_did_sdk_python.utils.cache.Cache.get")
            mock_cache_get.return_value = MOCK_SCHEMA

            registry = HederaAnonCredsRegistry(mock_client)

            resolution_result = await registry.get_schema(MOCK_SCHEMA_ID)
            assert resolution_result.schema == MOCK_SCHEMA

            mock_cache_get.assert_called_once_with(MOCK_SCHEMA_TOPIC_ID)

    class TestCredDef:
        async def test_resolves_cred_def_hcs_file(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
        ):
            mock_hcs_file_service.resolve_file.return_value = MOCK_CRED_DEF.to_json().encode()

            registry = HederaAnonCredsRegistry(mock_client)
            cred_def_resolution_result = await registry.get_cred_def(MOCK_CRED_DEF_ID)

            assert cred_def_resolution_result == GetCredDefResult(
                credential_definition=MOCK_CRED_DEF,
                credential_definition_id=MOCK_CRED_DEF_ID,
                resolution_metadata={},
                credential_definition_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_CRED_DEF_TOPIC_ID)

        async def test_resolve_returns_not_found(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
        ):
            mock_hcs_file_service.resolve_file.return_value = None

            registry = HederaAnonCredsRegistry(mock_client)
            cred_def_resolution_result = await registry.get_cred_def(MOCK_CRED_DEF_ID)

            assert cred_def_resolution_result == GetCredDefResult(
                credential_definition_id=MOCK_CRED_DEF_ID,
                resolution_metadata={
                    "error": "notFound",
                    "message": f"AnonCreds credential definition with id '{MOCK_CRED_DEF_ID}' not found",
                },
                credential_definition_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_CRED_DEF_TOPIC_ID)

        async def test_resolve_returns_not_found_on_invalid_id(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
        ):
            registry = HederaAnonCredsRegistry(mock_client)
            cred_def_resolution_result = await registry.get_cred_def(MOCK_SCHEMA_ID)

            assert cred_def_resolution_result == GetCredDefResult(
                credential_definition_id=MOCK_SCHEMA_ID,
                resolution_metadata={
                    "error": "notFound",
                    "message": f"Credential definition id '{MOCK_SCHEMA_ID}' is invalid",
                },
                credential_definition_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_not_awaited()

        async def test_registers_cred_def_as_hcs_file(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
        ):
            mock_hcs_file_service.submit_file.return_value = MOCK_CRED_DEF_TOPIC_ID

            registry = HederaAnonCredsRegistry(mock_client)
            cred_def_registration_result = await registry.register_cred_def(MOCK_CRED_DEF, OPERATOR_KEY_DER)

            assert cred_def_registration_result == RegisterCredDefResult(
                credential_definition_state=CredDefState(
                    state="finished",
                    credential_definition=MOCK_CRED_DEF,
                    credential_definition_id=build_anoncreds_identifier(
                        ISSUER_ID, MOCK_CRED_DEF_TOPIC_ID, AnonCredsObjectType.PUBLIC_CRED_DEF
                    ),
                ),
                registration_metadata={},
                credential_definition_metadata={},
            )

            mock_hcs_file_service.submit_file.assert_awaited_once()
            mock_hcs_file_service.submit_file.assert_awaited_with(MOCK_CRED_DEF.to_json().encode(), OPERATOR_KEY_DER)

        async def test_resolve_hits_cache(self, mock_client: Client, mocker: MockerFixture):
            mock_cache_get = mocker.patch("hiero_did_sdk_python.utils.cache.Cache.get")
            mock_cache_get.return_value = MOCK_CRED_DEF

            registry = HederaAnonCredsRegistry(mock_client)

            resolution_result = await registry.get_cred_def(MOCK_CRED_DEF_ID)
            assert resolution_result.credential_definition == MOCK_CRED_DEF

            mock_cache_get.assert_called_once_with(MOCK_CRED_DEF_TOPIC_ID)

    class TestRevRegDef:
        async def test_resolves_rev_reg_def_hcs_file(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
        ):
            mock_hcs_file_service.resolve_file.return_value = MOCK_REV_REG_DEF_WITH_METADATA.to_json().encode()

            registry = HederaAnonCredsRegistry(mock_client)
            resolution_result = await registry.get_rev_reg_def(MOCK_REV_REG_DEF_ID)

            assert resolution_result == GetRevRegDefResult(
                revocation_registry_definition=MOCK_REV_REG_DEF,
                revocation_registry_definition_id=MOCK_REV_REG_DEF_ID,
                resolution_metadata={},
                revocation_registry_definition_metadata={**MOCK_REV_REG_DEF_WITH_METADATA.hcs_metadata},
            )

            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_REV_REG_DEF_TOPIC_ID)

        async def test_resolve_returns_not_found(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
        ):
            mock_hcs_file_service.resolve_file.return_value = None

            registry = HederaAnonCredsRegistry(mock_client)
            resolution_result = await registry.get_rev_reg_def(MOCK_REV_REG_DEF_ID)

            assert resolution_result == GetRevRegDefResult(
                revocation_registry_definition_id=MOCK_REV_REG_DEF_ID,
                resolution_metadata={
                    "error": "notFound",
                    "message": f"AnonCreds revocation registry with id '{MOCK_REV_REG_DEF_ID}' not found",
                },
                revocation_registry_definition_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_REV_REG_DEF_TOPIC_ID)

        async def test_resolve_returns_not_found_on_invalid_id(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
        ):
            registry = HederaAnonCredsRegistry(mock_client)
            resolution_result = await registry.get_rev_reg_def(MOCK_SCHEMA_ID)

            assert resolution_result == GetRevRegDefResult(
                revocation_registry_definition_id=MOCK_SCHEMA_ID,
                resolution_metadata={
                    "error": "notFound",
                    "message": f"Revocation registry id '{MOCK_SCHEMA_ID}' is invalid",
                },
                revocation_registry_definition_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_not_awaited()

        async def test_registers_reg_reg_def_as_hcs_file(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
            mock_hcs_topic_service: NonCallableMagicMock,
        ):
            mock_hcs_file_service.submit_file.return_value = MOCK_REV_REG_DEF_TOPIC_ID

            registry = HederaAnonCredsRegistry(mock_client)
            registration_result = await registry.register_rev_reg_def(MOCK_REV_REG_DEF, OPERATOR_KEY_DER)

            assert registration_result == RegisterRevRegDefResult(
                revocation_registry_definition_state=RevRegDefState(
                    state="finished",
                    revocation_registry_definition=MOCK_REV_REG_DEF,
                    revocation_registry_definition_id=build_anoncreds_identifier(
                        ISSUER_ID, MOCK_REV_REG_DEF_TOPIC_ID, AnonCredsObjectType.REV_REG
                    ),
                ),
                registration_metadata={},
                revocation_registry_definition_metadata={**MOCK_REV_REG_DEF_WITH_METADATA.hcs_metadata},
            )

            mock_hcs_file_service.submit_file.assert_awaited_once()
            mock_hcs_file_service.submit_file.assert_awaited_with(
                MOCK_REV_REG_DEF_WITH_METADATA.to_json().encode(), OPERATOR_KEY_DER
            )

        async def test_caches_registered_rev_reg_def(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
            mock_hcs_topic_service: NonCallableMagicMock,
        ):
            mock_hcs_file_service.submit_file.return_value = MOCK_REV_REG_DEF_TOPIC_ID

            cache_instance = MemoryCache[str, object]()
            registry = HederaAnonCredsRegistry(mock_client, cache_instance)
            registration_result = await registry.register_rev_reg_def(MOCK_REV_REG_DEF, OPERATOR_KEY_DER)

            assert registration_result.revocation_registry_definition_state.state == "finished"

            cached_rev_reg_def = cache_instance.get(MOCK_REV_REG_DEF_TOPIC_ID)
            assert cached_rev_reg_def == MOCK_REV_REG_DEF_WITH_METADATA

        async def test_resolve_hits_cache(self, mock_client: Client, mocker: MockerFixture):
            mock_cache_get = mocker.patch("hiero_did_sdk_python.utils.cache.Cache.get")
            mock_cache_get.return_value = MOCK_REV_REG_DEF_WITH_METADATA

            registry = HederaAnonCredsRegistry(mock_client)

            resolution_result = await registry.get_rev_reg_def(MOCK_REV_REG_DEF_ID)
            assert resolution_result.revocation_registry_definition == MOCK_REV_REG_DEF

            mock_cache_get.assert_called_once_with(MOCK_REV_REG_DEF_TOPIC_ID)

    class TestRevList:
        async def test_resolves_rev_list(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
            mock_hcs_message_resolver: NonCallableMagicMock,
            mock_rev_list: AnonCredsRevList,
        ):
            mock_hcs_file_service.resolve_file.return_value = MOCK_REV_REG_DEF_WITH_METADATA.to_json().encode()

            registry = HederaAnonCredsRegistry(mock_client)
            resolution_result = await registry.get_rev_list(MOCK_REV_REG_DEF_ID, int(time.time()))

            assert resolution_result == GetRevListResult(
                revocation_list=mock_rev_list,
                revocation_registry_id=MOCK_REV_REG_DEF_ID,
                resolution_metadata={},
                revocation_list_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_REV_REG_DEF_TOPIC_ID)

            mock_hcs_message_resolver.execute.assert_awaited_once()

        async def test_resolve_returns_not_found_if_rev_def_is_missing(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
            mock_hcs_message_resolver: NonCallableMagicMock,
        ):
            mock_hcs_file_service.resolve_file.return_value = None

            registry = HederaAnonCredsRegistry(mock_client)
            resolution_result = await registry.get_rev_list(MOCK_REV_REG_DEF_ID, int(time.time()))

            assert resolution_result == GetRevListResult(
                revocation_registry_id=MOCK_REV_REG_DEF_ID,
                resolution_metadata={
                    "error": "notFound",
                    "message": f"AnonCreds revocation registry with id '{MOCK_REV_REG_DEF_ID}' not found",
                },
                revocation_list_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_REV_REG_DEF_TOPIC_ID)

            mock_hcs_message_resolver.execute.assert_not_awaited()

        async def test_resolve_returns_not_found_if_entries_topic_id_is_missing(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
            mock_hcs_message_resolver: NonCallableMagicMock,
        ):
            mock_reg_def_with_missing_metadata = RevRegDefWithHcsMetadata(rev_reg_def=MOCK_REV_REG_DEF, hcs_metadata={})  # pyright: ignore [reportArgumentType]
            mock_hcs_file_service.resolve_file.return_value = mock_reg_def_with_missing_metadata.to_json().encode()

            registry = HederaAnonCredsRegistry(mock_client)
            resolution_result = await registry.get_rev_list(MOCK_REV_REG_DEF_ID, int(time.time()))

            assert resolution_result == GetRevListResult(
                revocation_registry_id=MOCK_REV_REG_DEF_ID,
                resolution_metadata={
                    "error": "notFound",
                    "message": "Entries topic ID is missing from revocation registry metadata",
                },
                revocation_list_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_REV_REG_DEF_TOPIC_ID)

            mock_hcs_message_resolver.execute.assert_not_awaited()

        async def test_resolve_returns_initial_list(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
            mock_hcs_message_resolver: NonCallableMagicMock,
            Something,
        ):
            mock_hcs_file_service.resolve_file.return_value = MOCK_REV_REG_DEF_WITH_METADATA.to_json().encode()
            mock_hcs_message_resolver.execute.side_effect = [
                [],
                [MOCK_REV_ENTRY_MESSAGES_WITH_METADATA[0]],
            ]

            registry = HederaAnonCredsRegistry(mock_client)
            resolution_result = await registry.get_rev_list(MOCK_REV_REG_DEF_ID, int(time.time()))

            assert resolution_result == GetRevListResult(
                revocation_registry_id=MOCK_REV_REG_DEF_ID,
                revocation_list=AnonCredsRevList.from_rev_reg_entries(
                    entries=[MOCK_REV_ENTRY_1],
                    rev_reg_id=MOCK_REV_REG_DEF_ID,
                    rev_reg_def=MOCK_REV_REG_DEF,
                    timestamp=Something,
                ),
                resolution_metadata={},
                revocation_list_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_REV_REG_DEF_TOPIC_ID)

            mock_hcs_message_resolver.execute.assert_awaited()

        async def test_returns_not_found_if_entries_are_missing(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
            mock_hcs_message_resolver: NonCallableMagicMock,
        ):
            mock_hcs_file_service.resolve_file.return_value = MOCK_REV_REG_DEF_WITH_METADATA.to_json().encode()
            mock_hcs_message_resolver.execute.return_value = []

            registry = HederaAnonCredsRegistry(mock_client)
            resolution_result = await registry.get_rev_list(MOCK_REV_REG_DEF_ID, int(time.time()))

            assert resolution_result == GetRevListResult(
                revocation_registry_id=MOCK_REV_REG_DEF_ID,
                resolution_metadata={
                    "error": "notFound",
                    "message": f"Registered revocation list for registry id '{MOCK_REV_REG_DEF_ID}' is not found",
                },
                revocation_list_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_REV_REG_DEF_TOPIC_ID)

            mock_hcs_message_resolver.execute.assert_awaited()

        async def test_registers_rev_list(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
            mock_hcs_message_transaction: NonCallableMagicMock,
            mock_rev_list: AnonCredsRevList,
        ):
            mock_hcs_file_service.resolve_file.return_value = MOCK_REV_REG_DEF_WITH_METADATA.to_json().encode()

            registry = HederaAnonCredsRegistry(mock_client)
            registration_result = await registry.register_rev_list(mock_rev_list, OPERATOR_KEY_DER)

            assert registration_result == RegisterRevListResult(
                revocation_list_state=RevListState(state="finished", revocation_list=mock_rev_list),
                registration_metadata={},
                revocation_list_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_REV_REG_DEF_TOPIC_ID)

        async def test_updates_rev_list(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
            mock_hcs_message_transaction: NonCallableMagicMock,
            mock_rev_list: AnonCredsRevList,
            mock_rev_list_previous: AnonCredsRevList,
        ):
            mock_hcs_file_service.resolve_file.return_value = MOCK_REV_REG_DEF_WITH_METADATA.to_json().encode()

            registry = HederaAnonCredsRegistry(mock_client)
            registration_result = await registry.update_rev_list(
                mock_rev_list_previous,
                mock_rev_list,
                [*MOCK_REV_ENTRY_3.value.revoked],  # pyright: ignore [reportOptionalIterable]
                OPERATOR_KEY_DER,
            )

            assert registration_result == RegisterRevListResult(
                revocation_list_state=RevListState(state="finished", revocation_list=mock_rev_list),
                registration_metadata={},
                revocation_list_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_REV_REG_DEF_TOPIC_ID)

            mock_hcs_message_transaction.execute.assert_awaited_once()

        async def test_register_or_update_fail_if_rev_def_is_missing(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
            mock_hcs_message_transaction: NonCallableMagicMock,
            mock_rev_list: AnonCredsRevList,
            mock_rev_list_previous: AnonCredsRevList,
        ):
            mock_hcs_file_service.resolve_file.return_value = None

            registry = HederaAnonCredsRegistry(mock_client)
            registration_result = await registry.register_rev_list(mock_rev_list, OPERATOR_KEY_DER)

            assert registration_result == RegisterRevListResult(
                revocation_list_state=RevListState(
                    state="failed",
                    revocation_list=mock_rev_list,
                    reason=f"AnonCreds revocation registry with id '{mock_rev_list.rev_reg_def_id}' not found",
                ),
                registration_metadata={},
                revocation_list_metadata={},
            )

            update_result = await registry.update_rev_list(
                mock_rev_list_previous,
                mock_rev_list,
                [*MOCK_REV_ENTRY_3.value.revoked],  # pyright: ignore [reportOptionalIterable]
                OPERATOR_KEY_DER,
            )

            assert update_result == RegisterRevListResult(
                revocation_list_state=RevListState(
                    state="failed",
                    revocation_list=mock_rev_list,
                    reason=f"AnonCreds revocation registry with id '{mock_rev_list.rev_reg_def_id}' not found",
                ),
                registration_metadata={},
                revocation_list_metadata={},
            )

            assert mock_hcs_file_service.resolve_file.await_count == 2
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_REV_REG_DEF_TOPIC_ID)

            mock_hcs_message_transaction.execute.assert_not_awaited()

        async def test_register_or_update_fail_if_entries_topic_id_is_missing(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
            mock_hcs_message_transaction: NonCallableMagicMock,
            mock_rev_list: AnonCredsRevList,
            mock_rev_list_previous: AnonCredsRevList,
        ):
            mock_reg_def_with_missing_metadata = RevRegDefWithHcsMetadata(rev_reg_def=MOCK_REV_REG_DEF, hcs_metadata={})  # pyright: ignore [reportArgumentType]
            mock_hcs_file_service.resolve_file.return_value = mock_reg_def_with_missing_metadata.to_json().encode()

            registry = HederaAnonCredsRegistry(mock_client)
            registration_result = await registry.register_rev_list(mock_rev_list, OPERATOR_KEY_DER)

            assert registration_result == RegisterRevListResult(
                revocation_list_state=RevListState(
                    state="failed",
                    revocation_list=mock_rev_list,
                    reason="notFound: Entries topic ID is missing from revocation registry metadata",
                ),
                registration_metadata={},
                revocation_list_metadata={},
            )

            update_result = await registry.update_rev_list(
                mock_rev_list_previous,
                mock_rev_list,
                [*MOCK_REV_ENTRY_3.value.revoked],  # pyright: ignore [reportOptionalIterable]
                OPERATOR_KEY_DER,
            )

            assert update_result == RegisterRevListResult(
                revocation_list_state=RevListState(
                    state="failed",
                    revocation_list=mock_rev_list,
                    reason="notFound: Entries topic ID is missing from revocation registry metadata",
                ),
                registration_metadata={},
                revocation_list_metadata={},
            )

            # Resolved value is cached under the hood
            mock_hcs_file_service.resolve_file.assert_awaited_once()
            mock_hcs_file_service.resolve_file.assert_awaited_with(MOCK_REV_REG_DEF_TOPIC_ID)

            mock_hcs_message_transaction.execute.assert_not_awaited()

        async def test_resolves_previous_state_from_cache(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
            mock_hcs_message_resolver: NonCallableMagicMock,
            mock_rev_list_previous: AnonCredsRevList,
            mock_cache_instance: NonCallableMagicMock,
        ):
            mock_cache_instance.get.side_effect = [
                MOCK_REV_REG_DEF_WITH_METADATA,
                MOCK_REV_ENTRY_MESSAGES_WITH_METADATA,
            ]

            registry = HederaAnonCredsRegistry(mock_client, mock_cache_instance)
            resolution_result = await registry.get_rev_list(MOCK_REV_REG_DEF_ID, 200)

            assert resolution_result == GetRevListResult(
                revocation_list=mock_rev_list_previous,
                revocation_registry_id=MOCK_REV_REG_DEF_ID,
                resolution_metadata={},
                revocation_list_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_not_awaited()

            mock_cache_instance.get.assert_has_calls([
                call(MOCK_REV_REG_DEF_TOPIC_ID),
                call(MOCK_REV_REG_ENTRIES_TOPIC_ID),
            ])

            mock_hcs_message_resolver.execute.assert_not_awaited()

        async def test_resolves_future_state_using_cache(
            self,
            mock_client: Client,
            mock_hcs_file_service: NonCallableMagicMock,
            mock_hcs_message_resolver: NonCallableMagicMock,
            mock_rev_list: AnonCredsRevList,
            mock_cache_instance: NonCallableMagicMock,
        ):
            mock_cache_instance.get.side_effect = [
                MOCK_REV_REG_DEF_WITH_METADATA,
                MOCK_REV_ENTRY_MESSAGES_WITH_METADATA[:-1],
            ]
            mock_hcs_message_resolver.execute.return_value = [MOCK_REV_ENTRY_MESSAGES_WITH_METADATA[-1]]

            registry = HederaAnonCredsRegistry(mock_client, mock_cache_instance)
            resolution_result = await registry.get_rev_list(MOCK_REV_REG_DEF_ID, 300)

            assert resolution_result == GetRevListResult(
                revocation_list=mock_rev_list,
                revocation_registry_id=MOCK_REV_REG_DEF_ID,
                resolution_metadata={},
                revocation_list_metadata={},
            )

            mock_hcs_file_service.resolve_file.assert_not_awaited()

            mock_cache_instance.get.assert_has_calls([
                call(MOCK_REV_REG_DEF_TOPIC_ID),
                call(MOCK_REV_REG_ENTRIES_TOPIC_ID),
            ])

            mock_hcs_message_resolver.execute.assert_awaited_once()
