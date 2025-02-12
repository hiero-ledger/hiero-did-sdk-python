import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from threading import Lock
from typing import final, override

seconds = float

DEFAULT_TTL: seconds = float(3600)


@dataclass
class TimestampedRecord[T]:
    """Helper model for timestamped records.

    Attributes:
        data: Record data (generic)
        timestamp: Timestamp of record creation
    """

    data: T
    timestamp: float = field(default_factory=time.time)


class Cache[K, V](ABC):
    """Interface for cache instances used across SDK. Can be used to create custom cache implementations."""

    def __init__(self):
        self._locks = {}

    def _get_lock(self, key: K) -> Lock:
        if key not in self._locks:
            self._locks[key] = Lock()

        return self._locks[key]

    @final
    def get(self, key: K) -> V | None:
        """Get cached data by key

        Args:
            key: Cached data key

        Returns:
            object: Cached data
        """

        lock = self._get_lock(key)

        with lock:
            return self.data_get(key)

    @final
    def set(self, key: K, value: V, ttl: seconds | None = None) -> None:
        """Set cached data with key

        Args:
            key: Data key
            value: Data to cache
            ttl: Data retention duration in seconds.
        """
        ttl = ttl or DEFAULT_TTL

        lock = self._get_lock(key)

        with lock:
            self.data_set(key, value, ttl)

    @final
    def remove(self, key: K) -> None:
        """Remove cached data by key.

        Args:
            key: Cached data key
        """
        lock = self._get_lock(key)

        with lock:
            self.data_remove(key)

    @final
    def size(self):
        """Get cached records count."""
        return self.data_size()

    @final
    def flush(self):
        """Clear cached data."""
        return self.data_flush()

    @abstractmethod
    def data_get(self, key: K) -> V | None:
        pass

    @abstractmethod
    def data_set(self, key: K, value: V, ttl):
        pass

    @abstractmethod
    def data_remove(self, key: K):
        pass

    @abstractmethod
    def data_size(self) -> int:
        pass

    @abstractmethod
    def data_flush(self):
        pass


class MemoryCache[K, V](Cache[K, V]):
    """In-memory cache implementation. Includes built-in data retention logic."""

    def __init__(self):
        super().__init__()
        self._mem: dict[K, TimestampedRecord[V]] = {}

    # Cache clearing logic goes to child class because different classes can use different strategies
    # For example, Redis would use its built-in key TTL mechanic
    def _remove_expired_cached_items(self):
        for key in self._mem.copy():
            value = self._mem.get(key, None)

            # Assure value is still there, in multithreaded environment
            if value is not None:
                expires_timestamp = value.timestamp
                now = time.time()

                if now > expires_timestamp:
                    self.data_remove(key)

    @override
    def data_get(self, key: K) -> V | None:
        self._remove_expired_cached_items()

        record = self._mem.get(key, None)

        if record is None:
            return None

        return record.data

    @override
    def data_set(self, key: K, value: V, ttl: seconds):
        self._remove_expired_cached_items()

        expires_timestamp = time.time() + ttl
        self._mem[key] = TimestampedRecord(value, expires_timestamp)

    @override
    def data_size(self):
        return len(self._mem)

    @override
    def data_remove(self, key):
        # del wouldn't be thread safe
        self._mem.pop(key, None)

    @override
    def data_flush(self):
        self._mem = {}
