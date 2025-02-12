import logging
from typing import cast

from ..utils.ipfs import download_ipfs_document_by_cid
from ..utils.serializable import Serializable
from .did_document_operation import DidDocumentOperation
from .did_syntax import DID_DOCUMENT_CONTEXT, DidDocumentJsonProperties
from .hcs.events.document.hcs_did_create_did_document_event import HcsDidCreateDidDocumentEvent
from .hcs.events.hcs_did_event_target import HcsDidEventTarget
from .hcs.events.owner.hcs_did_update_did_owner_event import HcsDidUpdateDidOwnerEvent
from .hcs.events.service.hcs_did_revoke_service_event import HcsDidRevokeServiceEvent
from .hcs.events.service.hcs_did_update_service_event import HcsDidUpdateServiceEvent
from .hcs.events.verification_method.hcs_did_revoke_verification_method_event import HcsDidRevokeVerificationMethodEvent
from .hcs.events.verification_method.hcs_did_update_verification_method_event import HcsDidUpdateVerificationMethodEvent
from .hcs.events.verification_relationship.hcs_did_update_verification_relationship_event import (
    HcsDidUpdateVerificationRelationshipEvent,
)
from .hcs.hcs_did_message import HcsDidMessage

LOGGER = logging.getLogger(__name__)


class DidDocument(Serializable):
    """DID document representation

    Attributes:
        created: Creation timestamp
        updated: Last update timestamp
        version_id: DID document version ID (equals to last update timestamp)
        deactivated: DID document deactivation status
        controller: Dictionary representing DID document controller info
        services: DID document services dictionary
        verification_methods: DID document verification methods dictionary
        verification_methods: DID document verification relationships dictionary

    """

    def __init__(self, id_: str):
        self.id_ = id_
        self.context = DID_DOCUMENT_CONTEXT

        self.created: float | None = None
        self.updated: float | None = None
        self.version_id: str | None = None
        self.deactivated: bool = False

        self.controller: dict | None = None
        self.services: dict = {}
        self.verification_methods: dict = {}

        self.verification_relationships: dict = {
            DidDocumentJsonProperties.AUTHENTICATION.value: [],
            DidDocumentJsonProperties.ASSERTION_METHOD.value: [],
            DidDocumentJsonProperties.KEY_AGREEMENT.value: [],
            DidDocumentJsonProperties.CAPABILITY_INVOCATION.value: [],
            DidDocumentJsonProperties.CAPABILITY_DELEGATION.value: [],
        }

    async def process_messages(self, messages: list[HcsDidMessage]):
        """
        Process HCS DID messages - apply DID document state changes according to events.

        Args:
            messages: HCS DID messages to process

        """
        for message in messages:
            if not self.controller and message.operation == DidDocumentOperation.CREATE:
                event_target = message.event.event_target
                if event_target != HcsDidEventTarget.DID_OWNER and event_target != HcsDidEventTarget.DID_DOCUMENT:
                    LOGGER.warning("DID document is not registered, skipping DID update event...")
                    continue

            match message.operation:
                case DidDocumentOperation.CREATE:
                    await self._process_create_message(message)
                case DidDocumentOperation.UPDATE:
                    self._process_update_message(message)
                case DidDocumentOperation.DELETE:
                    self._process_delete_message(message)
                case DidDocumentOperation.REVOKE:
                    self._process_revoke_message(message)
                case _:
                    LOGGER.warning(f"Operation {message.operation} is not supported, skipping DID event...")

    @classmethod
    def from_json_payload(cls, payload: dict):
        raise Exception("DidDocument deserialization is not implemented")

    def get_json_payload(self):
        root_object: dict = {
            DidDocumentJsonProperties.CONTEXT.value: self.context,
            DidDocumentJsonProperties.ID.value: self.id_,
        }

        if self.controller and self.id_ != self.controller.get("controller"):
            root_object[DidDocumentJsonProperties.CONTROLLER.value] = (
                self.controller.get("controller") or self.controller
            )

        root_object[DidDocumentJsonProperties.VERIFICATION_METHOD.value] = list(self.verification_methods.values())

        root_object[DidDocumentJsonProperties.ASSERTION_METHOD.value] = [
            *self.verification_relationships[DidDocumentJsonProperties.ASSERTION_METHOD.value],
        ]

        root_object[DidDocumentJsonProperties.AUTHENTICATION.value] = [
            *self.verification_relationships[DidDocumentJsonProperties.AUTHENTICATION.value],
        ]

        if self.controller:
            controller_id = self.controller.get("id")

            root_object[DidDocumentJsonProperties.VERIFICATION_METHOD.value].insert(0, self.controller)
            root_object[DidDocumentJsonProperties.ASSERTION_METHOD.value].insert(0, controller_id)
            root_object[DidDocumentJsonProperties.AUTHENTICATION.value].insert(0, controller_id)

        if len(self.verification_relationships[DidDocumentJsonProperties.KEY_AGREEMENT.value]) > 0:
            root_object[DidDocumentJsonProperties.KEY_AGREEMENT.value] = [
                *self.verification_relationships[DidDocumentJsonProperties.KEY_AGREEMENT.value],
            ]
        if len(self.verification_relationships[DidDocumentJsonProperties.CAPABILITY_INVOCATION.value]) > 0:
            root_object[DidDocumentJsonProperties.CAPABILITY_INVOCATION.value] = [
                *self.verification_relationships[DidDocumentJsonProperties.CAPABILITY_INVOCATION.value],
            ]
        if len(self.verification_relationships[DidDocumentJsonProperties.CAPABILITY_DELEGATION.value]) > 0:
            root_object[DidDocumentJsonProperties.CAPABILITY_DELEGATION.value] = [
                *self.verification_relationships[DidDocumentJsonProperties.CAPABILITY_DELEGATION.value],
            ]

        if len(self.services) > 0:
            root_object[DidDocumentJsonProperties.SERVICE.value] = list(self.services.values())

        return root_object

    async def _process_create_message(self, message: HcsDidMessage):  # noqa: C901
        event = message.event

        match event.event_target:
            case HcsDidEventTarget.DID_DOCUMENT:
                document = await download_ipfs_document_by_cid(cast(HcsDidCreateDidDocumentEvent, event).cid)

                if document[DidDocumentJsonProperties.ID] != self.id_:
                    raise ValueError("Document ID does not match did")

                self.controller = document[DidDocumentJsonProperties.CONTROLLER]

                self.services = {
                    service["id"]: service for service in document.get(DidDocumentJsonProperties.SERVICE, [])
                }

                self.verification_methods = {
                    verificationMethod["id"]: verificationMethod
                    for verificationMethod in document.get(DidDocumentJsonProperties.VERIFICATION_METHOD, [])
                }

                self.verification_relationships[DidDocumentJsonProperties.ASSERTION_METHOD] = document.get(
                    DidDocumentJsonProperties.ASSERTION_METHOD, []
                )
                self.verification_relationships[DidDocumentJsonProperties.AUTHENTICATION] = document.get(
                    DidDocumentJsonProperties.AUTHENTICATION, []
                )
                self.verification_relationships[DidDocumentJsonProperties.KEY_AGREEMENT] = document.get(
                    DidDocumentJsonProperties.KEY_AGREEMENT, []
                )
                self.verification_relationships[DidDocumentJsonProperties.CAPABILITY_INVOCATION] = document.get(
                    DidDocumentJsonProperties.CAPABILITY_INVOCATION, []
                )
                self.verification_relationships[DidDocumentJsonProperties.CAPABILITY_DELEGATION] = document.get(
                    DidDocumentJsonProperties.CAPABILITY_DELEGATION, []
                )
            case HcsDidEventTarget.DID_OWNER:
                if self.controller:
                    LOGGER.warning(f"DID owner is already registered: {self.controller}, skipping event...")
                    return

                self.controller = cast(HcsDidUpdateDidOwnerEvent, event).get_owner_def()
                self._on_activated(message.timestamp)
            case HcsDidEventTarget.SERVICE:
                update_service_event = cast(HcsDidUpdateServiceEvent, event)
                event_id = update_service_event.id_

                if event_id in self.services:
                    LOGGER.warning(f"Duplicate create Service event ID: {event_id}, skipping event...")
                    return

                self.services[event_id] = update_service_event.get_service_def()
                self._on_updated(message.timestamp)
            case HcsDidEventTarget.VERIFICATION_METHOD:
                update_verification_method_event = cast(HcsDidUpdateVerificationMethodEvent, event)
                event_id = update_verification_method_event.id_

                if event_id in self.verification_methods:
                    LOGGER.warning(f"Duplicate create Verification Method event ID: {event_id}, skipping event...")
                    return

                self.verification_methods[event_id] = update_verification_method_event.get_verification_method_def()
                self._on_updated(message.timestamp)
            case HcsDidEventTarget.VERIFICATION_RELATIONSHIP:
                update_verification_relationship_event = cast(HcsDidUpdateVerificationRelationshipEvent, event)
                relationship_type = update_verification_relationship_event.relationship_type
                event_id = update_verification_relationship_event.id_

                if relationship_type not in self.verification_relationships:
                    LOGGER.warning(
                        f"Create verification Relationship event with type {relationship_type} is not supported, skipping event..."
                    )
                    return

                if event_id in self.verification_relationships[relationship_type]:
                    LOGGER.warning(
                        f"Duplicate create Verification Relationship event ID: {event_id}, skipping event..."
                    )
                    return

                self.verification_relationships[relationship_type].append(event_id)

                if event_id not in self.verification_methods:
                    self.verification_methods[event_id] = (
                        update_verification_relationship_event.get_verification_method_def()
                    )
                self._on_updated(message.timestamp)
            case _:
                LOGGER.warning(f"Create {event.event_target} operation is not supported, skipping event...")

    def _process_update_message(self, message: HcsDidMessage):
        event = message.event

        match event.event_target:
            case HcsDidEventTarget.DID_OWNER:
                self.controller = cast(HcsDidUpdateDidOwnerEvent, event).get_owner_def()
                self._on_updated(message.timestamp)
            case HcsDidEventTarget.SERVICE:
                update_service_event = cast(HcsDidUpdateServiceEvent, event)
                event_id = update_service_event.id_

                if event_id not in self.services:
                    LOGGER.warning(f"Service with ID: {event_id} is not found on the document, skipping event...")
                    return

                self.services[event_id] = update_service_event.get_service_def()
                self._on_updated(message.timestamp)
            case HcsDidEventTarget.VERIFICATION_METHOD:
                update_verification_method_event = cast(HcsDidUpdateVerificationMethodEvent, event)
                event_id = update_verification_method_event.id_

                if event_id not in self.verification_methods:
                    LOGGER.warning(
                        f"Verification Method with ID: {event_id} is not found on the document, skipping event..."
                    )
                    return

                self.verification_methods[event_id] = update_verification_method_event.get_verification_method_def()
                self._on_updated(message.timestamp)
            case HcsDidEventTarget.VERIFICATION_RELATIONSHIP:
                update_verification_relationship_event = cast(HcsDidUpdateVerificationRelationshipEvent, event)
                relationship_type = update_verification_relationship_event.relationship_type
                event_id = update_verification_relationship_event.id_

                if relationship_type not in self.verification_relationships:
                    LOGGER.warning(
                        f"Update verification Relationship event with type {relationship_type} is not supported, skipping event..."
                    )
                    return

                if event_id not in self.verification_relationships[relationship_type]:
                    LOGGER.warning(
                        f"Verification Relationship with ID: {event_id} is not found on the document, skipping event..."
                    )
                    return

                self.verification_methods[event_id] = (
                    update_verification_relationship_event.get_verification_method_def()
                )
                self._on_updated(message.timestamp)
            case _:
                LOGGER.warning(f"Update {event.event_target} operation is not supported, skipping event...")

    def _process_revoke_message(self, message: HcsDidMessage):
        event = message.event

        match event.event_target:
            case HcsDidEventTarget.SERVICE:
                revoke_service_event = cast(HcsDidRevokeServiceEvent, event)
                event_id = revoke_service_event.id_

                if event_id not in self.services:
                    LOGGER.warning(f"Service with ID: {event_id} is not found on the document, skipping event...")
                    return

                del self.services[event_id]
                self._on_updated(message.timestamp)
            case HcsDidEventTarget.VERIFICATION_METHOD:
                revoke_verification_method_event = cast(HcsDidRevokeVerificationMethodEvent, event)
                event_id = revoke_verification_method_event.id_

                if event_id not in self.verification_methods:
                    LOGGER.warning(
                        f"Verification Method with ID: {event_id} is not found on the document, skipping event..."
                    )
                    return

                del self.verification_methods[event_id]

                for type_key in self.verification_relationships:
                    self.verification_relationships[type_key] = list(
                        filter(lambda id_: id_ != event_id, self.verification_relationships[type_key])
                    )

                self._on_updated(message.timestamp)
            case HcsDidEventTarget.VERIFICATION_RELATIONSHIP:
                revoke_verification_relationship_event = cast(HcsDidUpdateVerificationRelationshipEvent, event)
                relationship_type = revoke_verification_relationship_event.relationship_type
                event_id = revoke_verification_relationship_event.id_

                if relationship_type not in self.verification_relationships:
                    LOGGER.warning(
                        f"Revoke verification Relationship event with type {relationship_type} is not supported, skipping event..."
                    )
                    return

                if event_id not in self.verification_relationships[relationship_type]:
                    LOGGER.warning(
                        f"Verification Relationship with ID: {event_id} is not found on the document, skipping event..."
                    )
                    return

                self.verification_relationships[relationship_type] = list(
                    filter(lambda id_: id_ != event_id, self.verification_relationships[relationship_type])
                )

                can_delete_verification_method = all(
                    event_id not in rel for rel in self.verification_relationships.values()
                )

                if can_delete_verification_method:
                    del self.verification_methods[event_id]

                self._on_updated(message.timestamp)
            case _:
                LOGGER.warning(f"Revoke {event.event_target} operation is not supported, skipping event...")

    def _process_delete_message(self, message: HcsDidMessage):
        event = message.event

        match event.event_target:
            case HcsDidEventTarget.DOCUMENT:
                self.controller = None
                self.services.clear()
                self.verification_methods.clear()
                for type_key in self.verification_relationships:
                    self.verification_relationships[type_key] = []
                self._on_deactivated()
            case _:
                LOGGER.warning(f"Delete {event.event_target} operation is not supported, skipping event...")

    def _on_activated(self, timestamp: float):
        self.created = timestamp
        self.updated = timestamp
        self.deactivated = False
        self.version_id = str(timestamp)

    def _on_updated(self, timestamp: float):
        self.updated = timestamp
        self.version_id = str(timestamp)

    def _on_deactivated(self):
        self.created = None
        self.updated = None
        self.deactivated = True
        self.version_id = None
