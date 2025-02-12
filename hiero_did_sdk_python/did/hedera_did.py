import logging
from typing import Literal, cast

from hiero_sdk_python import Client, PrivateKey, PublicKey, TopicMessageSubmitTransaction
from hiero_sdk_python.transaction.transaction import Transaction

from ..hcs import HcsMessageResolver, HcsMessageTransaction, HcsTopicOptions, HcsTopicService
from ..hcs.constants import MAX_TRANSACTION_FEE
from ..utils.encoding import multibase_encode
from ..utils.keys import get_key_type
from .did_document import DidDocument
from .did_document_operation import DidDocumentOperation
from .did_error import DidException
from .hcs import HcsDidMessageEnvelope
from .hcs.events import HcsDidEvent
from .hcs.events.document import HcsDidDeleteEvent
from .hcs.events.owner import HcsDidUpdateDidOwnerEvent
from .hcs.events.service import HcsDidRevokeServiceEvent, HcsDidUpdateServiceEvent
from .hcs.events.verification_method import HcsDidRevokeVerificationMethodEvent, HcsDidUpdateVerificationMethodEvent
from .hcs.events.verification_relationship import (
    HcsDidRevokeVerificationRelationshipEvent,
    HcsDidUpdateVerificationRelationshipEvent,
)
from .hcs.hcs_did_message import HcsDidMessage
from .types import (
    DidServiceType,
    SupportedKeyType,
    VerificationRelationshipType,
)
from .utils import build_identifier, parse_identifier

LOGGER = logging.getLogger(__name__)


class HederaDid:
    """
    Class representing Hedera DID instance, provides access to DID management API.

    Args:
        client: Hedera Client
        identifier: DID identifier (for existing DIDs)
        private_key_der: DID Owner (controller) private key encoded in DER format. Can be empty for read-only access
    """

    def __init__(self, client: Client, identifier: str | None = None, private_key_der: str | None = None):
        if not identifier and not private_key_der:
            raise DidException("'identifier' and 'private_key_der' cannot both be empty")

        self._client = client
        self._hcs_topic_service = HcsTopicService(client)

        self._private_key = PrivateKey.from_string(private_key_der) if private_key_der else None
        self._key_type: SupportedKeyType | None = (
            cast(SupportedKeyType, get_key_type(self._private_key)) if self._private_key else None
        )

        self.identifier = identifier
        if self.identifier:
            parsed_identifier = parse_identifier(self.identifier)
            self.network = parsed_identifier.network
            self.topic_id = parsed_identifier.topic_id
        else:
            self.topic_id = None

        self._messages: list[HcsDidMessage] = []
        self.document: DidDocument | None = None

    async def register(self):
        """Register (create) DID instance in Hedera network"""
        if not self._private_key or not self._key_type:
            raise DidException("Private key is required to register new DID")

        if self.identifier:
            document = await self.resolve()
            if document.controller:
                raise DidException("DID is already registered")
        else:
            topic_options = HcsTopicOptions(
                admin_key=self._private_key.public_key(), submit_key=self._private_key.public_key()
            )

            self.topic_id = await self._hcs_topic_service.create_topic(topic_options, [self._private_key])

            self.network = self._client.network.network
            self.identifier = build_identifier(
                self.network,
                multibase_encode(bytes(self._private_key.public_key().to_bytes_raw()), "base58btc"),
                self.topic_id,
            )

        hcs_event = HcsDidUpdateDidOwnerEvent(
            id_=f"{self.identifier}#did-root-key",
            controller=self.identifier,
            public_key=self._private_key.public_key(),
            type_=self._key_type,
        )

        await self._submit_transaction(DidDocumentOperation.CREATE, hcs_event)

    async def change_owner(self, controller: str, new_private_key_der: str):
        """
        Change DID Owner (controller).

        Args:
            controller: Identifier of new DID Owner
            new_private_key_der: New DID Owner private key encoded in DER format
        """
        self._assert_can_submit_transaction()

        document = await self.resolve()
        if not document.controller:
            raise DidException("DID is not registered or was recently deleted. DID has to be registered first")

        new_private_key = PrivateKey.from_string(new_private_key_der)
        new_key_type = get_key_type(new_private_key)

        topic_update_options = HcsTopicOptions(
            admin_key=new_private_key.public_key(), submit_key=new_private_key.public_key()
        )
        await self._hcs_topic_service.update_topic(
            cast(str, self.topic_id), topic_update_options, [cast(PrivateKey, self._private_key), new_private_key]
        )

        self._private_key = new_private_key
        self._key_type = new_key_type

        hcs_event = HcsDidUpdateDidOwnerEvent(
            id_=f"{self.identifier}#did-root-key",
            controller=controller,
            public_key=self._private_key.public_key(),
            type_=self._key_type,
        )

        await self._submit_transaction(DidDocumentOperation.UPDATE, hcs_event)

    async def resolve(self) -> DidDocument:
        """
        Resolve DID document for registered instance.

        Returns:
            object: DID document
        """
        if not self.topic_id or not self.identifier:
            raise DidException("DID is not registered")

        result = await HcsMessageResolver(self.topic_id, HcsDidMessageEnvelope).execute(self._client)
        await self._handle_resolution_result(cast(list[HcsDidMessageEnvelope], result))

        return cast(DidDocument, self.document)

    async def delete(self):
        """Delete (deactivate) registered DID instance."""
        self._assert_can_submit_transaction()

        await self._submit_transaction(DidDocumentOperation.DELETE, HcsDidDeleteEvent())

    async def add_service(self, id_: str, service_type: DidServiceType, service_endpoint: str):
        """Add Service to DID document

        Args:
            id_: Service ID to create
            service_type: DID service type
            service_endpoint: Service endpoint
        """
        await self._add_or_update_service(
            DidDocumentOperation.CREATE, id_=id_, type_=service_type, service_endpoint=service_endpoint
        )

    async def update_service(self, id_: str, service_type: DidServiceType, service_endpoint: str):
        """Update existing DID document service

        Args:
            id_: Service ID to update
            service_type: DID service type
            service_endpoint: Service endpoint
        """
        await self._add_or_update_service(
            DidDocumentOperation.UPDATE, id_=id_, type_=service_type, service_endpoint=service_endpoint
        )

    async def revoke_service(self, id_: str):
        """Revoke existing DID document service

        Args:
            id_: Service ID to revoke
        """
        self._assert_can_submit_transaction()

        hcs_event = HcsDidRevokeServiceEvent(id_)
        await self._submit_transaction(DidDocumentOperation.REVOKE, hcs_event)

    async def add_verification_method(
        self,
        id_: str,
        controller: str,
        public_key_der: str,
        type_: SupportedKeyType,
    ):
        """Add verification method to DID document

        Args:
            id_: Verification method ID to create
            controller: Verification method controller ID
            public_key_der: Verification method public key encoded in DER format
            type_: Verification method key type
        """
        await self._add_or_update_verification_method(
            DidDocumentOperation.CREATE,
            id_=id_,
            controller=controller,
            public_key=PublicKey.from_string(public_key_der),
            type_=type_,
        )

    async def update_verification_method(
        self,
        id_: str,
        controller: str,
        public_key_der: str,
        type_: SupportedKeyType,
    ):
        """Update existing DID document verification method

        Args:
            id_: Verification method ID to update
            controller: Verification method controller ID
            public_key_der: Verification method public key encoded in DER format
            type_: Verification method key type
        """
        await self._add_or_update_verification_method(
            DidDocumentOperation.UPDATE,
            id_=id_,
            controller=controller,
            public_key=PublicKey.from_string(public_key_der),
            type_=type_,
        )

    async def revoke_verification_method(self, id_: str):
        """Revoke existing DID document verification method

        Args:
            id_: Verification method ID to revoke
        """
        self._assert_can_submit_transaction()

        hcs_event = HcsDidRevokeVerificationMethodEvent(id_)
        await self._submit_transaction(DidDocumentOperation.REVOKE, hcs_event)

    async def add_verification_relationship(
        self,
        id_: str,
        controller: str,
        public_key_der: str,
        relationship_type: VerificationRelationshipType,
        type_: SupportedKeyType,
    ):
        """Add verification relationship to DID document

        Args:
            id_: Verification relationship ID to create
            controller: Verification relationship controller ID
            public_key_der: Verification relationship public key encoded in DER format
            relationship_type: Verification relationship type
            type_: Verification relationship key type
        """
        await self._add_or_update_verification_relationship(
            DidDocumentOperation.CREATE,
            id_=id_,
            controller=controller,
            public_key=PublicKey.from_string(public_key_der),
            relationship_type=relationship_type,
            type_=type_,
        )

    async def update_verification_relationship(
        self,
        id_: str,
        controller: str,
        public_key_der: str,
        relationship_type: VerificationRelationshipType,
        type_: SupportedKeyType,
    ):
        """Update existing DID document verification relationship

        Args:
            id_: Verification relationship ID to update
            controller: Verification relationship controller ID
            public_key_der: Verification relationship public key encoded in DER format
            relationship_type: Verification relationship type
            type_: Verification relationship key type
        """
        await self._add_or_update_verification_relationship(
            DidDocumentOperation.UPDATE,
            id_=id_,
            public_key=PublicKey.from_string(public_key_der),
            controller=controller,
            relationship_type=relationship_type,
            type_=type_,
        )

    async def revoke_verification_relationship(self, id_: str, relationship_type: VerificationRelationshipType):
        """Revoke existing DID document verification relationship

        Args:
            id_: Verification relationship ID to revoke
            relationship_type: Verification relationship type
        """
        self._assert_can_submit_transaction()

        hcs_event = HcsDidRevokeVerificationRelationshipEvent(id_, relationship_type)
        await self._submit_transaction(DidDocumentOperation.REVOKE, hcs_event)

    async def _submit_transaction(self, operation: DidDocumentOperation, event: HcsDidEvent):
        if not self.topic_id or not self.identifier or not self._private_key:
            raise Exception("Cannot submit transaction: topic_id, identifier and private_key must be set")

        message = HcsDidMessage(operation, self.identifier, event)
        envelope = HcsDidMessageEnvelope(message)
        envelope.sign(self._private_key)

        def build_did_transaction(message_submit_transaction: TopicMessageSubmitTransaction) -> Transaction:
            message_submit_transaction.transaction_fee = MAX_TRANSACTION_FEE.to_tinybars()  # pyright: ignore [reportAttributeAccessIssue]
            return message_submit_transaction.freeze_with(self._client).sign(self._private_key)

        await HcsMessageTransaction(self.topic_id, envelope, build_did_transaction).execute(self._client)

    async def _add_or_update_service(
        self, operation: Literal[DidDocumentOperation.CREATE, DidDocumentOperation.UPDATE], **kwargs
    ):
        self._assert_can_submit_transaction()

        await self._submit_transaction(operation, HcsDidUpdateServiceEvent(**kwargs))

    async def _add_or_update_verification_method(
        self, operation: Literal[DidDocumentOperation.CREATE, DidDocumentOperation.UPDATE], **kwargs
    ):
        self._assert_can_submit_transaction()

        await self._submit_transaction(operation, HcsDidUpdateVerificationMethodEvent(**kwargs))

    async def _add_or_update_verification_relationship(
        self, operation: Literal[DidDocumentOperation.CREATE, DidDocumentOperation.UPDATE], **kwargs
    ):
        self._assert_can_submit_transaction()

        await self._submit_transaction(operation, HcsDidUpdateVerificationRelationshipEvent(**kwargs))

    async def _handle_resolution_result(self, result: list[HcsDidMessageEnvelope]):
        if not self.identifier:
            raise Exception("Cannot handle DID resolution result: DID identifier is not defined")

        self._messages = [cast(HcsDidMessage, envelope.message) for envelope in result]
        self.document = DidDocument(self.identifier)
        await self.document.process_messages(self._messages)

    def _assert_can_submit_transaction(self):
        if not self.identifier:
            raise DidException("DID is not registered")

        if not self._private_key or not self._key_type:
            raise DidException("Private key is required to submit DID event transaction")
