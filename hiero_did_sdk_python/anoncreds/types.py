from dataclasses import dataclass
from typing import Literal

from .models import AnonCredsCredDef, AnonCredsRevList, AnonCredsRevRegDef, AnonCredsSchema

ObjectState = Literal["finished", "failed", "action", "wait"]


@dataclass(frozen=True)
class SchemaState:
    """Schema state model.

    Attributes:
        state: Object state
        schema: Schema object
        schema_id: Schema ID
        reason: Reason (relevant for operation failures)
    """

    state: ObjectState
    schema: AnonCredsSchema
    schema_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class RegisterSchemaResult:
    """Schema registration result model.

    Attributes:
        schema_state: Schema Object state
        registration_metadata: Registration metadata
        schema_metadata: Schema object metadata
    """

    schema_state: SchemaState
    registration_metadata: dict
    schema_metadata: dict


@dataclass(frozen=True)
class GetSchemaResult:
    """Schema resolution result model.

    Attributes:
        schema_id: Schema ID
        resolution_metadata: Resolution metadata
        schema_metadata: Schema object metadata
        schema: Schema object (empty if resolution is not successful)
    """

    schema_id: str
    resolution_metadata: dict
    schema_metadata: dict
    schema: AnonCredsSchema | None = None


@dataclass(frozen=True)
class CredDefState:
    """Credential definition state model.

    Attributes:
        state: Object state
        credential_definition: Credential definition object
        credential_definition_id: Credential definition ID
        reason: Reason (relevant for operation failures)
    """

    state: ObjectState
    credential_definition: AnonCredsCredDef
    credential_definition_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class RegisterCredDefResult:
    """Credential definition registration result model.

    Attributes:
        credential_definition_state: Credential definition Object state
        registration_metadata: Registration metadata
        credential_definition_metadata: Credential definition object metadata
    """

    credential_definition_state: CredDefState
    registration_metadata: dict
    credential_definition_metadata: dict


@dataclass(frozen=True)
class GetCredDefResult:
    """Credential definition resolution result model.

    Attributes:
        credential_definition_id: Credential definition ID
        resolution_metadata: Resolution metadata
        credential_definition_metadata: Credential definition object metadata
        credential_definition: Credential definition object (empty if resolution is not successful)
    """

    credential_definition_id: str
    resolution_metadata: dict
    credential_definition_metadata: dict
    credential_definition: AnonCredsCredDef | None = None


@dataclass(frozen=True)
class RevRegDefState:
    """Revocation registry definition state model.

    Attributes:
        state: Object state
        revocation_registry_definition: Revocation registry definition object
        revocation_registry_definition_id: Revocation registry definition ID
        reason: Reason (relevant for operation failures)
    """

    state: ObjectState
    revocation_registry_definition: AnonCredsRevRegDef
    revocation_registry_definition_id: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class RegisterRevRegDefResult:
    """Revocation registry definition registration result model.

    Attributes:
        revocation_registry_definition_state: Revocation registry definition Object state
        registration_metadata: Registration metadata
        revocation_registry_definition_metadata: Revocation registry definition object metadata
    """

    revocation_registry_definition_state: RevRegDefState
    registration_metadata: dict
    revocation_registry_definition_metadata: dict


@dataclass(frozen=True)
class GetRevRegDefResult:
    """Revocation registry definition resolution result model.

    Attributes:
        revocation_registry_definition_id: Revocation registry definition ID
        resolution_metadata: Resolution metadata
        revocation_registry_definition_metadata: Revocation registry definition object metadata
        revocation_registry_definition: Revocation registry definition object (empty if resolution is not successful)
    """

    revocation_registry_definition_id: str
    resolution_metadata: dict
    revocation_registry_definition_metadata: dict
    revocation_registry_definition: AnonCredsRevRegDef | None = None


@dataclass(frozen=True)
class RevListState:
    """Revocation list state model.

    Attributes:
        state: Object state
        revocation_list: Revocation list object
        reason: Reason (relevant for operation failures)
    """

    state: ObjectState
    revocation_list: AnonCredsRevList
    reason: str | None = None


@dataclass(frozen=True)
class RegisterRevListResult:
    """Revocation list registration result model.

    Attributes:
        revocation_list_state: Revocation list Object state
        registration_metadata: Registration metadata
        revocation_list_metadata: Revocation list object metadata
    """

    revocation_list_state: RevListState
    registration_metadata: dict
    revocation_list_metadata: dict


@dataclass(frozen=True)
class GetRevListResult:
    """Revocation list resolution result model.

    Attributes:
        revocation_registry_id: Revocation list ID
        resolution_metadata: Resolution metadata
        revocation_list_metadata: Revocation list object metadata
        revocation_list: Revocation list object (empty if resolution is not successful)
    """

    revocation_registry_id: str
    resolution_metadata: dict
    revocation_list_metadata: dict
    revocation_list: AnonCredsRevList | None = None
