"""Tests for the bounded worker pool."""

import threading
from concurrent.futures import ThreadPoolExecutor

from app.core.worker_pool import get_executor, shutdown_executor


class TestWorkerPool:
    def teardown_method(self):
        shutdown_executor()

    def test_get_executor_returns_pool(self):
        executor = get_executor()
        assert isinstance(executor, ThreadPoolExecutor)

    def test_get_executor_singleton(self):
        first = get_executor()
        second = get_executor()
        assert first is second

    def test_shutdown_and_recreate(self):
        first = get_executor()
        shutdown_executor()
        second = get_executor()
        assert first is not second

    def test_submit_runs_function(self):
        event = threading.Event()
        executor = get_executor()
        future = executor.submit(event.set)
        future.result(timeout=5)
        assert event.is_set()
