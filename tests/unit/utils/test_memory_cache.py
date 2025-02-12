import threading
import time
from collections.abc import Callable

import pytest

from hiero_did_sdk_python.utils.cache import Cache, MemoryCache

thread_id = int


def _multithread_perform(action: Callable[[thread_id], None], count: int):
    threads = []

    for i in range(1, count + 1):
        t = threading.Thread(target=action, args=(i,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


def _insert_upto(cache: Cache[int, str], num):
    for n in range(1, num + 1):
        cache.set(n, str(n))


@pytest.fixture(scope="function")
def cache():
    return MemoryCache[int, str]()


@pytest.fixture(scope="function")
def num_cache():
    return MemoryCache[int, int]()


class TestMemoryCache:
    def test_empty_size(self, cache):
        assert cache.size() == 0

    def test_insert_retrieve(self, cache):
        _insert_upto(cache, 5)

        assert cache.size() == 5
        assert cache.get(1) == "1"
        assert cache.get(2) == "2"
        assert cache.get(3) == "3"
        assert cache.get(4) == "4"
        assert cache.get(5) == "5"

    def test_insert_remove_retrieve(self, cache):
        _insert_upto(cache, 5)

        cache.remove(1)
        cache.remove(3)

        assert cache.size() == 3
        assert cache.get(1) is None
        assert cache.get(2) == "2"
        assert cache.get(3) is None
        assert cache.get(4) == "4"
        assert cache.get(5) == "5"

    def test_insert_flush(self, cache):
        _insert_upto(cache, 5)

        cache.flush()

        assert cache.size() == 0
        assert cache.get(1) is None
        assert cache.get(2) is None
        assert cache.get(3) is None
        assert cache.get(4) is None
        assert cache.get(5) is None

    def test_not_empty(self, cache):
        _insert_upto(cache, 1)

        assert cache.size() > 0

    def test_multithread_insertion_separate_domain(self, cache):
        def _insert_data(thread_id: thread_id):
            hundreds_digit = thread_id
            start = hundreds_digit * 100
            end = start + 99

            for n in range(start, end + 1):
                cache.set(n, str(n))

        thread_count = 5

        _multithread_perform(_insert_data, thread_count)

        assert cache.size() == 500

        for n in range(0, 99 + 1):
            assert cache.get(n) is None

        for digit in range(1, thread_count + 1):
            start = digit * 100
            end = start + 99
            for n in range(start, end + 1):
                assert cache.get(n) == str(n)

    def test_multithread_retrieval_separate_domain(self, num_cache: Cache[int, int]):
        for n in range(0, 1000 + 1):
            num_cache.set(n, n)

        def _get_val_sum(_):
            total = 0
            for n in range(0, 1000 + 1):
                val = num_cache.get(n)

                if val is not None:
                    total += val

            assert total == 500500

        _multithread_perform(_get_val_sum, 5)

    def test_multithread_retrieval_same_domain(self, cache):
        for n in range(0, 1000 + 1):
            cache.set(n, n * 2)

        def _assert_double_of(_):
            for n in range(0, 1000 + 1):
                assert cache.get(n) == n * 2

        _multithread_perform(_assert_double_of, 5)

    def test_multithread_insertion_same_domain(self, cache):
        def _set_double_of(_):
            for n in range(0, 100 + 1):
                cache.set(n, n * 2)

        _multithread_perform(_set_double_of, 5)

        for n in range(0, 100 + 1):
            assert cache.get(n) == n * 2

    def test_multithread_retrieval_with_flush(self, cache):
        for n in range(0, 10000 + 1):
            cache.set(n, str(n))

        def _flush():
            time.sleep(1)
            cache.flush()

        def _get_if_exists():
            not_nones_count = 0
            nones_count = 0
            for n in range(0, 10000 + 1):
                val = cache.get(n)

                if val is not None:
                    not_nones_count += 1
                else:
                    nones_count += 1

            assert not_nones_count > 0
            assert nones_count > 0

        t1 = threading.Thread(target=_flush, args=())
        t2 = threading.Thread(target=_get_if_exists, args=())

        t1.start()
        t2.start()

        t1.join()
        t2.join()

    def test_short_ttl(self, cache):
        for n in range(0, 10000 + 1):
            cache.set(n, str(n), 0.01)

        for n in range(0, 10000 + 1):
            val = cache.get(n)

            assert val is None
