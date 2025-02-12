import logging
from collections.abc import Sequence
from itertools import chain
from typing import cast

from hiero_sdk_python import Client, PrivateKey, Timestamp, TopicMessageSubmitTransaction
from hiero_sdk_python.transaction.transaction import Transaction

from ..hcs import (
    HcsFileService,
    HcsMessageResolver,
    HcsMessageTransaction,
    HcsMessageWithResponseMetadata,
    HcsTopicOptions,
    HcsTopicService,
)
from ..hcs.constants import MAX_TRANSACTION_FEE
from ..utils.cache import Cache, MemoryCache
from .models import (
    AnonCredsCredDef,
    AnonCredsRevList,
    AnonCredsRevRegDef,
    AnonCredsRevRegEntry,
    AnonCredsSchema,
    HcsRevRegEntryMessage,
    RevRegDefWithHcsMetadata,
    RevRegEntryValue,
)
from .types import (
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
from .utils import AnonCredsObjectType, build_anoncreds_identifier, parse_anoncreds_identifier

LOGGER = logging.getLogger(__name__)


class HederaAnonCredsRegistry:
    """Anoncreds objects registry (resolver + registrar) implementation that leverage Hedera HCS as VDR.

    Args:
        client: Hedera Client
        cache_instance: Custom cache instance. If not provided, in-memory cache is used
    """

    def __init__(
        self,
        client: Client,
        cache_instance: Cache[str, object] | None = None,
    ):
        self._client = client
        self._hcs_file_service = HcsFileService(client)
        self._hcs_topic_service = HcsTopicService(client)

        cache_instance = cache_instance or MemoryCache[str, object]()

        self._schema_cache: Cache[str, AnonCredsSchema] = cast(Cache[str, AnonCredsSchema], cache_instance)
        self._cred_def_cache: Cache[str, AnonCredsCredDef] = cast(Cache[str, AnonCredsCredDef], cache_instance)
        self._rev_reg_def_cache: Cache[str, RevRegDefWithHcsMetadata] = cast(
            Cache[str, RevRegDefWithHcsMetadata], cache_instance
        )
        self._rev_reg_entries_messages_cache = cast(Cache[str, list[HcsMessageWithResponseMetadata]], cache_instance)

    async def get_schema(self, schema_id: str) -> GetSchemaResult:
        """Get a schema from the registry.

        Args:
            schema_id: Schema ID to resolver

        Returns:
            object: Schema resolution result
        """
        try:
            parsed_identifier = parse_anoncreds_identifier(schema_id)

            if parsed_identifier.object_type != AnonCredsObjectType.SCHEMA:
                return GetSchemaResult(
                    schema_id=schema_id,
                    resolution_metadata={
                        "error": "notFound",
                        "message": f"AnonCreds Schema id '{schema_id}' is invalid",
                    },
                    schema_metadata={},
                )

            schema_topic_id = parsed_identifier.topic_id

            cached_schema = self._schema_cache.get(schema_topic_id)

            if cached_schema:
                schema = cached_schema
            else:
                schema_payload = await self._hcs_file_service.resolve_file(parsed_identifier.topic_id)
                schema = AnonCredsSchema.from_json(schema_payload.decode()) if schema_payload else None

                if not schema:
                    return GetSchemaResult(
                        schema_id=schema_id,
                        resolution_metadata={
                            "error": "notFound",
                            "message": f"AnonCreds schema with id '{schema_id}' not found",
                        },
                        schema_metadata={},
                    )

                self._schema_cache.set(schema_topic_id, schema)

            return GetSchemaResult(schema=schema, schema_id=schema_id, resolution_metadata={}, schema_metadata={})
        except Exception as error:
            LOGGER.error(f"Error on retrieving AnonCreds Schema: {error!s}")
            return GetSchemaResult(
                schema_id=schema_id,
                resolution_metadata={
                    "error": "otherError",
                    "message": f"unable to resolve schema: ${error!s}",
                },
                schema_metadata={},
            )

    async def register_schema(self, schema: AnonCredsSchema, issuer_key_der: str) -> RegisterSchemaResult:
        """Register Schema.

        Args:
            schema: Schema object to register
            issuer_key_der: Issuer private key encoded in DER format

        Returns:
            object: Schema registration result
        """
        try:
            hcs_file_payload = schema.to_json().encode()
            schema_topic_id = await self._hcs_file_service.submit_file(hcs_file_payload, issuer_key_der)

            return RegisterSchemaResult(
                schema_state=SchemaState(
                    state="finished",
                    schema=schema,
                    schema_id=build_anoncreds_identifier(schema.issuer_id, schema_topic_id, AnonCredsObjectType.SCHEMA),
                ),
                schema_metadata={},
                registration_metadata={},
            )
        except Exception as error:
            LOGGER.error(f"Error on registering Anoncreds Schema: {error!s}")
            return RegisterSchemaResult(
                schema_state=SchemaState(state="failed", schema=schema, reason=f"unknownError: ${error!s}"),
                schema_metadata={},
                registration_metadata={},
            )

    async def get_cred_def(self, cred_def_id: str) -> GetCredDefResult:
        """Get a credential definition from the registry.

        Args:
            cred_def_id: Credential definition ID to resolve

        Returns:
            object: Credential definition resolution result
        """
        try:
            parsed_identifier = parse_anoncreds_identifier(cred_def_id)

            if parsed_identifier.object_type != AnonCredsObjectType.PUBLIC_CRED_DEF:
                return GetCredDefResult(
                    credential_definition_id=cred_def_id,
                    resolution_metadata={
                        "error": "notFound",
                        "message": f"Credential definition id '{cred_def_id}' is invalid",
                    },
                    credential_definition_metadata={},
                )

            cred_def_topic_id = parsed_identifier.topic_id

            cached_cred_def = self._cred_def_cache.get(cred_def_topic_id)

            if cached_cred_def:
                cred_def = cached_cred_def
            else:
                cred_def_payload = await self._hcs_file_service.resolve_file(cred_def_topic_id)
                cred_def = AnonCredsCredDef.from_json(cred_def_payload.decode()) if cred_def_payload else None

                if not cred_def:
                    return GetCredDefResult(
                        credential_definition_id=cred_def_id,
                        resolution_metadata={
                            "error": "notFound",
                            "message": f"AnonCreds credential definition with id '{cred_def_id}' not found",
                        },
                        credential_definition_metadata={},
                    )

                self._cred_def_cache.set(cred_def_topic_id, cred_def)

            return GetCredDefResult(
                credential_definition=cred_def,
                credential_definition_id=cred_def_id,
                resolution_metadata={},
                credential_definition_metadata={},
            )
        except Exception as error:
            LOGGER.error(f"Error on retrieving AnonCreds credential definition: {error!s}")
            return GetCredDefResult(
                credential_definition_id=cred_def_id,
                resolution_metadata={
                    "error": "otherError",
                    "message": f"unable to resolve credential definition: ${error!s}",
                },
                credential_definition_metadata={},
            )

    async def register_cred_def(self, cred_def: AnonCredsCredDef, issuer_key_der: str) -> RegisterCredDefResult:
        """Register Credential Definition.

        Args:
            cred_def: Credential definition object to register
            issuer_key_der: Issuer private key encoded in DER

        Returns:
            object: Credential definition registration result
        """
        try:
            hcs_file_payload = cred_def.to_json().encode()
            cred_def_topic_id = await self._hcs_file_service.submit_file(hcs_file_payload, issuer_key_der)

            return RegisterCredDefResult(
                credential_definition_state=CredDefState(
                    state="finished",
                    credential_definition=cred_def,
                    credential_definition_id=build_anoncreds_identifier(
                        cred_def.issuer_id, cred_def_topic_id, AnonCredsObjectType.PUBLIC_CRED_DEF
                    ),
                ),
                registration_metadata={},
                credential_definition_metadata={},
            )
        except Exception as error:
            LOGGER.error(f"Error on registering Anoncreds Cred Def: {error!s}")
            return RegisterCredDefResult(
                credential_definition_state=CredDefState(
                    state="failed", credential_definition=cred_def, reason=f"unknownError: ${error!s}"
                ),
                registration_metadata={},
                credential_definition_metadata={},
            )

    async def get_rev_reg_def(self, revocation_registry_definition_id: str) -> GetRevRegDefResult:
        """Get a revocation registry definition from the registry.

        Args:
            revocation_registry_definition_id: Revocation registry definition ID to resolve

        Returns:
            object: Revocation registry definition resolution result
        """
        try:
            parsed_identifier = parse_anoncreds_identifier(revocation_registry_definition_id)

            if parsed_identifier.object_type != AnonCredsObjectType.REV_REG:
                return GetRevRegDefResult(
                    revocation_registry_definition_id=revocation_registry_definition_id,
                    resolution_metadata={
                        "error": "notFound",
                        "message": f"Revocation registry id '{revocation_registry_definition_id}' is invalid",
                    },
                    revocation_registry_definition_metadata={},
                )

            rev_reg_def_topic_id = parsed_identifier.topic_id

            cached_rev_reg_def_with_metadata = self._rev_reg_def_cache.get(rev_reg_def_topic_id)

            if cached_rev_reg_def_with_metadata:
                rev_reg_def_with_metadata = cached_rev_reg_def_with_metadata
            else:
                rev_reg_def_payload = await self._hcs_file_service.resolve_file(rev_reg_def_topic_id)
                rev_reg_def_with_metadata = (
                    RevRegDefWithHcsMetadata.from_json(rev_reg_def_payload.decode()) if rev_reg_def_payload else None
                )

                if not rev_reg_def_with_metadata:
                    return GetRevRegDefResult(
                        revocation_registry_definition_id=revocation_registry_definition_id,
                        resolution_metadata={
                            "error": "notFound",
                            "message": f"AnonCreds revocation registry with id '{revocation_registry_definition_id}' not found",
                        },
                        revocation_registry_definition_metadata={},
                    )

                self._rev_reg_def_cache.set(rev_reg_def_topic_id, rev_reg_def_with_metadata)

            return GetRevRegDefResult(
                revocation_registry_definition=rev_reg_def_with_metadata.rev_reg_def,
                revocation_registry_definition_id=revocation_registry_definition_id,
                resolution_metadata={},
                revocation_registry_definition_metadata={**rev_reg_def_with_metadata.hcs_metadata},
            )
        except Exception as error:
            LOGGER.error(f"Error on retrieving AnonCreds revocation registry definition: {error!s}")
            return GetRevRegDefResult(
                revocation_registry_definition_id=revocation_registry_definition_id,
                resolution_metadata={
                    "error": "otherError",
                    "message": f"unable to resolve revocation registry definition: ${error!s}",
                },
                revocation_registry_definition_metadata={},
            )

    async def register_rev_reg_def(
        self, rev_reg_def: AnonCredsRevRegDef, issuer_key_der: str
    ) -> RegisterRevRegDefResult:
        """Register Revocation registry definition.

        Args:
            rev_reg_def: Revocation registry definition object to register
            issuer_key_der: Issuer private key encoded in DER

        Returns:
            object: Revocation registry definition registration result
        """
        try:
            issuer_key = PrivateKey.from_string(issuer_key_der)

            entries_topic_options = HcsTopicOptions(submit_key=issuer_key.public_key())
            entries_topic_id = await self._hcs_topic_service.create_topic(entries_topic_options, [issuer_key])

            rev_reg_def_with_metadata = RevRegDefWithHcsMetadata(
                rev_reg_def=rev_reg_def, hcs_metadata={"entries_topic_id": entries_topic_id}
            )

            hcs_file_payload = rev_reg_def_with_metadata.to_json().encode()
            rev_reg_def_topic_id = await self._hcs_file_service.submit_file(hcs_file_payload, issuer_key_der)

            # We want to cache registry definition right away
            # Helps to avoid potential cases where issuer pushes rev entries immediately but registry definition data (HCS-1 messages) is not propagated to mirror nodes yet
            self._rev_reg_def_cache.set(rev_reg_def_topic_id, rev_reg_def_with_metadata)

            return RegisterRevRegDefResult(
                revocation_registry_definition_state=RevRegDefState(
                    state="finished",
                    revocation_registry_definition=rev_reg_def,
                    revocation_registry_definition_id=build_anoncreds_identifier(
                        rev_reg_def.issuer_id, rev_reg_def_topic_id, AnonCredsObjectType.REV_REG
                    ),
                ),
                registration_metadata={},
                revocation_registry_definition_metadata={**rev_reg_def_with_metadata.hcs_metadata},
            )
        except Exception as error:
            LOGGER.error(f"Error on registering Anoncreds Revocation registry definition: {error!s}")
            return RegisterRevRegDefResult(
                revocation_registry_definition_state=RevRegDefState(
                    state="failed", revocation_registry_definition=rev_reg_def, reason=f"unknownError: ${error!s}"
                ),
                registration_metadata={},
                revocation_registry_definition_metadata={},
            )

    async def get_rev_list(self, rev_reg_id: str, timestamp: int) -> GetRevListResult:
        """Get a revocation list from the registry.

        Args:
            rev_reg_id: Revocation registry ID
            timestamp: Timestamp to resolve revocation list for

        Returns:
            object: Revocation list resolution result
        """
        try:
            rev_reg_def_result = await self.get_rev_reg_def(rev_reg_id)

            if not rev_reg_def_result.revocation_registry_definition:
                return GetRevListResult(
                    revocation_registry_id=rev_reg_id,
                    resolution_metadata={
                        "error": "notFound",
                        "message": f"AnonCreds revocation registry with id '{rev_reg_id}' not found",
                    },
                    revocation_list_metadata={},
                )

            rev_reg_def = rev_reg_def_result.revocation_registry_definition
            entries_topic_id = rev_reg_def_result.revocation_registry_definition_metadata.get("entries_topic_id")

            if not entries_topic_id:
                return GetRevListResult(
                    revocation_registry_id=rev_reg_id,
                    resolution_metadata={
                        "error": "notFound",
                        "message": "Entries topic ID is missing from revocation registry metadata",
                    },
                    revocation_list_metadata={},
                )

            cached_messages = self._rev_reg_entries_messages_cache.get(entries_topic_id)
            if cached_messages:
                last_cached_message_timestamp = cached_messages[-1].consensus_timestamp

                if last_cached_message_timestamp.seconds >= timestamp:
                    borderline_timestamp = Timestamp(seconds=timestamp, nanos=0)
                    entries_messages = filter(
                        lambda message: message.consensus_timestamp.seconds < timestamp
                        or message.consensus_timestamp == borderline_timestamp,
                        cached_messages,
                    )
                    entries = [cast(AnonCredsRevRegEntry, message.message) for message in entries_messages]

                    # This means that requested timestamp is before the actual registration of rev list
                    # In such case, we want to return initial state for the list (by adding first message to entries)
                    if len(entries) == 0:
                        entries.append(cast(AnonCredsRevRegEntry, cached_messages[0].message))

                    return GetRevListResult(
                        revocation_registry_id=rev_reg_id,
                        revocation_list=AnonCredsRevList.from_rev_reg_entries(
                            entries, rev_reg_id, rev_reg_def, timestamp
                        ),
                        resolution_metadata={},
                        revocation_list_metadata={},
                    )
                else:
                    new_messages = await HcsMessageResolver(
                        topic_id=entries_topic_id,
                        message_type=HcsRevRegEntryMessage,
                        timestamp_from=last_cached_message_timestamp,
                        timestamp_to=Timestamp(seconds=timestamp, nanos=0),
                        include_response_metadata=True,
                    ).execute(self._client)

                    # Note: 'chain' function is used instead of lists sum due to significantly better performance on large lists
                    # See: https://docs.python.org/3/library/itertools.html, https://stackoverflow.com/a/41772165
                    entries_messages = (
                        list(chain(cached_messages, cast(list[HcsMessageWithResponseMetadata], new_messages)))
                        if len(new_messages) > 0
                        else cached_messages
                    )

                    self._rev_reg_entries_messages_cache.set(entries_topic_id, entries_messages)

                    entries = [cast(AnonCredsRevRegEntry, message.message) for message in entries_messages]

                    return GetRevListResult(
                        revocation_registry_id=rev_reg_id,
                        revocation_list=AnonCredsRevList.from_rev_reg_entries(
                            entries, rev_reg_id, rev_reg_def, timestamp
                        ),
                        resolution_metadata={},
                        revocation_list_metadata={},
                    )

            entries_messages = await HcsMessageResolver(
                topic_id=entries_topic_id,
                message_type=HcsRevRegEntryMessage,
                timestamp_to=Timestamp(seconds=timestamp, nanos=0),
                include_response_metadata=True,
            ).execute(self._client)

            if len(entries_messages) == 0:
                # If returned entries list is empty, we need to fetch the first message and check if list is registered
                # It's possible that requested timestamp is before the actual registration of rev list -> we want to return initial state for the list (by adding first message to entries)

                # The second request looks redundant here, but it should be the rare case that will be subsequently handled by cache
                entries_messages = await HcsMessageResolver(
                    topic_id=entries_topic_id,
                    message_type=HcsRevRegEntryMessage,
                    limit=1,
                    include_response_metadata=True,
                ).execute(self._client)

                if len(entries_messages) == 0:
                    return GetRevListResult(
                        revocation_registry_id=rev_reg_id,
                        resolution_metadata={
                            "error": "notFound",
                            "message": f"Registered revocation list for registry id '{rev_reg_id}' is not found",
                        },
                        revocation_list_metadata={},
                    )

            entries_messages = cast(list[HcsMessageWithResponseMetadata], entries_messages)
            self._rev_reg_entries_messages_cache.set(entries_topic_id, entries_messages)

            entries = [cast(AnonCredsRevRegEntry, message.message) for message in entries_messages]

            return GetRevListResult(
                revocation_registry_id=rev_reg_id,
                revocation_list=AnonCredsRevList.from_rev_reg_entries(entries, rev_reg_id, rev_reg_def, timestamp),
                resolution_metadata={},
                revocation_list_metadata={},
            )

        except Exception as error:
            LOGGER.error(f"Error on retrieving AnonCreds revocation list: {error!s}")
            return GetRevListResult(
                revocation_registry_id=rev_reg_id,
                resolution_metadata={
                    "error": "otherError",
                    "message": f"Unable to resolve revocation list: ${error!s}",
                },
                revocation_list_metadata={},
            )

    async def register_rev_list(self, rev_list: AnonCredsRevList, issuer_key_der: str) -> RegisterRevListResult:
        """Register Revocation list.

        Args:
            rev_list: Revocation list object to register
            issuer_key_der: Issuer private key encoded in DER

        Returns: Revocation list registration result
        """
        try:
            return await self._submit_rev_list_entry(rev_list, issuer_key_der)
        except Exception as error:
            LOGGER.error(f"Error on registering Anoncreds revocation list: {error!s}")
            return RegisterRevListResult(
                revocation_list_state=RevListState(
                    state="failed", revocation_list=rev_list, reason=f"unknownError: ${error!s}"
                ),
                registration_metadata={},
                revocation_list_metadata={},
            )

    async def update_rev_list(
        self, prev_list: AnonCredsRevList, curr_list: AnonCredsRevList, revoked: Sequence[int], issuer_key_der: str
    ) -> RegisterRevListResult:
        """Update Revocation list.

        Args:
            prev_list: Previous Revocation list object
            curr_list: Current Revocation list object
            revoked: Revoked credential indexes
            issuer_key_der: Issuer private key encoded in DER

        Returns: Revocation list update result
        """
        try:
            return await self._submit_rev_list_entry(curr_list, issuer_key_der, prev_list, revoked)
        except Exception as error:
            LOGGER.error(f"Error on updating Anoncreds revocation list: {error!s}")
            return RegisterRevListResult(
                revocation_list_state=RevListState(
                    state="failed", revocation_list=curr_list, reason=f"unknownError: ${error!s}"
                ),
                registration_metadata={},
                revocation_list_metadata={},
            )

    async def _submit_rev_list_entry(
        self,
        rev_list: AnonCredsRevList,
        issuer_key_der: str,
        prev_list: AnonCredsRevList | None = None,
        revoked: Sequence[int] | None = None,
    ) -> RegisterRevListResult:
        if prev_list and prev_list.rev_reg_def_id != rev_list.rev_reg_def_id:
            return RegisterRevListResult(
                revocation_list_state=RevListState(
                    state="failed",
                    revocation_list=rev_list,
                    reason=f"Revocation registry ids do not match for previous and current list: '{prev_list.rev_reg_def_id}' != '{rev_list.rev_reg_def_id}'",
                ),
                registration_metadata={},
                revocation_list_metadata={},
            )

        rev_reg_def_result = await self.get_rev_reg_def(rev_list.rev_reg_def_id)

        if not rev_reg_def_result.revocation_registry_definition:
            return RegisterRevListResult(
                revocation_list_state=RevListState(
                    state="failed",
                    revocation_list=rev_list,
                    reason=f"AnonCreds revocation registry with id '{rev_list.rev_reg_def_id}' not found",
                ),
                registration_metadata={},
                revocation_list_metadata={},
            )

        entries_topic_id = rev_reg_def_result.revocation_registry_definition_metadata.get("entries_topic_id")

        if not entries_topic_id:
            return RegisterRevListResult(
                revocation_list_state=RevListState(
                    state="failed",
                    revocation_list=rev_list,
                    reason="notFound: Entries topic ID is missing from revocation registry metadata",
                ),
                registration_metadata={},
                revocation_list_metadata={},
            )

        entry_message = HcsRevRegEntryMessage(
            value=RevRegEntryValue(
                prev_accum=prev_list.current_accumulator if prev_list else None,
                accum=rev_list.current_accumulator,
                revoked=list(revoked) if revoked else None,
            )
        )

        def build_message_submit_transaction(
            message_submit_transaction: TopicMessageSubmitTransaction,
        ) -> Transaction:
            message_submit_transaction.transaction_fee = MAX_TRANSACTION_FEE.to_tinybars()  # pyright: ignore [reportAttributeAccessIssue]
            return message_submit_transaction.freeze_with(self._client).sign(PrivateKey.from_string(issuer_key_der))

        await HcsMessageTransaction(entries_topic_id, entry_message, build_message_submit_transaction).execute(
            self._client
        )

        return RegisterRevListResult(
            revocation_list_state=RevListState(state="finished", revocation_list=rev_list),
            registration_metadata={},
            revocation_list_metadata={},
        )
