import logging
from collections.abc import Callable

from hiero_sdk_python import Client, Timestamp, TopicId, TopicMessageQuery
from hiero_sdk_python.consensus.topic_message import TopicMessage

from .hcs_message import HcsMessage, HcsMessageWithResponseMetadata

LOGGER = logging.getLogger(__name__)


class HcsTopicListener:
    def __init__(
        self,
        topic_id: str,
        message_class: type[HcsMessage],
        include_response_metadata: bool = False,
    ):
        self.topic_id = topic_id
        self._message_class = message_class
        self._include_response_metadata = include_response_metadata
        self._filters = []
        self._subscription_handle = None
        self._invalid_message_handler = None
        self._error_handler = None

        self._query = (
            TopicMessageQuery(topic_id=TopicId.from_string(topic_id), start_time=Timestamp(0, 0).to_date())
            # Not implemented in native SDK
            # See GH issue: https://github.com/hiero-ledger/hiero-sdk-python/issues/43
            # .setMaxBackoff(JDuration.ofMillis(2000))
            # .setMaxAttempts(5)
        )

    def set_start_time(self, start_time: Timestamp):
        self._query.set_start_time(start_time.to_date())
        return self

    def set_end_time(self, end_time: Timestamp):
        self._query.set_end_time(end_time.to_date())
        return self

    def set_limit(self, limit: int):
        self._query.set_limit(limit)
        return self

    def set_completion_handler(self, completion_handler: Callable[[], None]):
        # Not implemented in native SDK
        # See GH issue: https://github.com/hiero-ledger/hiero-sdk-python/issues/43
        # self._query.setCompletionHandler(completion_handler)
        return self

    def add_filter(self, response_filter: Callable[[TopicMessage], bool]):
        self._filters.append(response_filter)
        return self

    def set_invalid_message_handler(self, invalid_message_handler: Callable[[TopicMessage, str], None]):
        self._invalid_message_handler = invalid_message_handler
        return self

    def subscribe(
        self,
        client: Client,
        receiver: Callable[[HcsMessage | HcsMessageWithResponseMetadata], None],
        error_handler: Callable[[Exception], None] | None = None,
    ):
        def handle_message(response):
            self._handle_response(response, receiver)

        # Subscription handle is not actually implemented in native SDK
        # See GH issue: https://github.com/hiero-ledger/hiero-sdk-python/issues/43
        self._subscription_handle = self._query.subscribe(client, handle_message, error_handler)

    def unsubscribe(self):
        if self._subscription_handle:
            self._subscription_handle.unsubscribe()

    def _handle_response(
        self, response: TopicMessage, receiver: Callable[[HcsMessage | HcsMessageWithResponseMetadata], None]
    ):
        if len(self._filters) > 0:
            for response_filter in self._filters:
                if not response_filter(response):
                    self._report_invalid_message(response, "Message response was rejected by user-defined filter")
                    return

        message = self._extract_message(response)
        if not message:
            self._report_invalid_message(response, "Extracting message from the mirror response failed")
            return

        if not message.is_valid(self.topic_id):
            self._report_invalid_message(response, "Extracted message is invalid")
            return

        if self._include_response_metadata:
            receiver(
                HcsMessageWithResponseMetadata(
                    message=message,
                    sequence_number=response.sequence_number,
                    consensus_timestamp=Timestamp.from_protobuf(response.consensus_timestamp),
                )
            )
        else:
            receiver(message)

    def _extract_message(self, response: TopicMessage) -> HcsMessage | None:
        try:
            return self._message_class.from_json(response.message.decode())
        except Exception as error:
            LOGGER.warning(f"Failed to extract HCS message from response: {error!s}")

    def _report_invalid_message(self, response: TopicMessage, reason: str):
        LOGGER.warning(f"Got invalid message: {response.message.decode()}, reason: {reason}")
        if self._invalid_message_handler:
            self._invalid_message_handler(response, reason)
