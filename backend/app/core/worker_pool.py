"""Bounded thread pool for background document processing.

Replaces unbounded ``threading.Thread`` calls with a
``ThreadPoolExecutor`` that limits concurrency to ``_MAX_WORKERS``.
"""

from concurrent.futures import ThreadPoolExecutor

# 4 workers leaves headroom for the PostgreSQL connection pool
# (default 5 + 10 overflow = 15 connections).
_MAX_WORKERS = 4

_executor: ThreadPoolExecutor | None = None


def get_executor() -> ThreadPoolExecutor:
    """Return the module-level executor, creating it lazily."""
    global _executor
    if _executor is None or _executor._shutdown:
        _executor = ThreadPoolExecutor(max_workers=_MAX_WORKERS)
    return _executor


def shutdown_executor() -> None:
    """Shut down the executor, waiting for running tasks to complete."""
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=True, cancel_futures=False)
        _executor = None
