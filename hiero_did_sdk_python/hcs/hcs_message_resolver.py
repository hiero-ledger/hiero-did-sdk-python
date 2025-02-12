import asyncio
import logging
import time
from asyncio import Future
from threading import Timer

from hiero_sdk_python import Client, Timestamp

from .hcs_message import HcsMessage, HcsMessageWithResponseMetadata
from .hcs_message_envelope import HcsMessageEnvelope
from .hcs_topic_listener import HcsTopicListener

DEFAULT_TIMEOUT_SECONDS = float(5)

TOPIC_UNSUBSCRIBED_ERROR = "CANCELLED: unsubscribe"

LOGGER = logging.getLogger(__name__)


class HcsMessageResolver:
    def __init__(
        self,
        topic_id: str,
        message_type: type[HcsMessage],
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        timestamp_from: Timestamp | None = None,
        timestamp_to: Timestamp | None = None,
        limit: int | None = None,
        include_response_metadata: bool = False,
    ):
        self.topic_id = topic_id
        self._topic_listener = HcsTopicListener(
            topic_id, message_type, include_response_metadata=include_response_metadata
        )
        self._message_type = message_type

        self._message_waiting_timeout = timeout_seconds
        self._last_message_arrival_time: float = time.time()

        self._timestamp_from = timestamp_from
        self._timestamp_to = timestamp_to
        self._limit = limit

        self._messages: list[HcsMessage | HcsMessageWithResponseMetadata] = []
        self._received_message_hashes: list[str] = []

        self._waiting_timer: Timer | None = None

    async def execute(self, client: Client) -> list[HcsMessage | HcsMessageWithResponseMetadata]:
        self._received_message_hashes = []

        completion_future = asyncio.get_running_loop().create_future()

        def handle_completion():
            self._complete(completion_future)

        def handle_error(error: Exception):
            if not completion_future.done() and str(error) != TOPIC_UNSUBSCRIBED_ERROR:
                completion_future.set_exception(error)

        if self._timestamp_from:
            self._topic_listener.set_start_time(self._timestamp_from)

        if self._limit:
            self._topic_listener.set_limit(self._limit)

        (
            self._topic_listener.set_end_time(self._timestamp_to or Timestamp(seconds=int(time.time()), nanos=0))
            .set_completion_handler(handle_completion)
            .subscribe(client, self._handle_message, handle_error)
        )

        self._last_message_arrival_time = time.time()
        self._wait_or_complete(completion_future)

        await completion_future

        return completion_future.result()

    def _handle_message(self, message: HcsMessage | HcsMessageWithResponseMetadata):
        self._last_message_arrival_time = time.time()

        if isinstance(message, HcsMessageEnvelope) and not message.signature:
            LOGGER.warning("Received message envelope with missing signature, skipping...")
            return

        message_hash = message.get_payload_hash()

        if message_hash in self._received_message_hashes:
            LOGGER.warning("Received message duplicate, skipping...")
            return

        self._received_message_hashes.append(message_hash)
        self._messages.append(message)

    def _complete(self, future: Future):
        future.get_loop().call_soon_threadsafe(future.set_result, self._messages)

        if self._waiting_timer:
            self._waiting_timer.cancel()

        self._topic_listener.unsubscribe()

    def _wait_or_complete(self, future: Future):
        time_diff = time.time() - self._last_message_arrival_time

        if time_diff <= self._message_waiting_timeout:
            if self._waiting_timer:
                self._waiting_timer.cancel()
            timer_interval = self._message_waiting_timeout - time_diff
            self._waiting_timer = Timer(timer_interval, self._wait_or_complete, [future])
            self._waiting_timer.start()
            return
        else:
            self._complete(future)
