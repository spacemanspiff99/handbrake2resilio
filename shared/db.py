"""Shared SQLite database helper with WAL mode, busy timeout, and write retries."""

from __future__ import annotations

import sqlite3
import time
from typing import Callable, Optional, TypeVar

T = TypeVar("T")

# Default wait (seconds) for sqlite3.connect when the database file is locked.
_DEFAULT_LOCK_WAIT_SECONDS = 30.0
# Default SQLite busy_handler timeout in milliseconds (PRAGMA busy_timeout).
_DEFAULT_BUSY_TIMEOUT_MS = 30000


def _is_locked_operational_error(exc: BaseException) -> bool:
    """Return True if *exc* is a lock-related SQLite operational error."""
    if not isinstance(exc, sqlite3.OperationalError):
        return False
    return "locked" in str(exc).lower()


def _retry_on_locked(
    operation: Callable[[], T],
    max_retries: int = 3,
    backoff: float = 1.0,
) -> T:
    """
    Run *operation*, retrying on lock-related OperationalError.

    Makes up to ``max_retries + 1`` attempts (initial try plus *max_retries* retries).
    """
    last_exc: Optional[sqlite3.OperationalError] = None
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except sqlite3.OperationalError as exc:
            if not _is_locked_operational_error(exc):
                raise
            last_exc = exc
            if attempt >= max_retries:
                raise
            time.sleep(backoff)
    assert last_exc is not None
    raise last_exc


def get_db_connection(
    db_path: str,
    timeout: int = _DEFAULT_BUSY_TIMEOUT_MS,
    *,
    lock_wait_seconds: float = _DEFAULT_LOCK_WAIT_SECONDS,
) -> sqlite3.Connection:
    """
    Open a SQLite connection with WAL journal mode and busy timeout.

    WAL mode allows concurrent readers with one writer, reducing
    ``database is locked`` errors when multiple services use the same file.

    Args:
        db_path: Path to the SQLite database file.
        timeout: ``PRAGMA busy_timeout`` value in **milliseconds** (default 30000).
        lock_wait_seconds: ``sqlite3.connect`` timeout in **seconds** (default 30).

    Returns:
        sqlite3.Connection with WAL mode and busy timeout set.
    """
    conn = sqlite3.connect(
        db_path,
        check_same_thread=False,
        timeout=lock_wait_seconds,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(f"PRAGMA busy_timeout={timeout};")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def execute_with_retry(
    conn: sqlite3.Connection,
    sql: str,
    params: tuple = (),
    max_retries: int = 3,
    backoff: float = 1.0,
) -> sqlite3.Cursor:
    """Execute a write SQL statement with retry on database lock.

    Args:
        conn: Open SQLite connection.
        sql: SQL statement to execute.
        params: Bind parameters.
        max_retries: Maximum number of retry attempts.
        backoff: Seconds to wait between retries.

    Returns:
        sqlite3.Cursor from the successful execute call.

    Raises:
        sqlite3.OperationalError: If all retries are exhausted.
    """
    import time

    last_err: sqlite3.OperationalError | None = None
    for attempt in range(max_retries + 1):
        try:
            return conn.execute(sql, params)
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower():
                raise
            last_err = exc
            if attempt < max_retries:
                time.sleep(backoff)
    raise last_err


def commit_with_retry(
    conn: sqlite3.Connection,
    max_retries: int = 3,
    backoff: float = 1.0,
) -> None:
    """
    Commit the current transaction, retrying on lock-related errors.

    Args:
        conn: Active SQLite connection.
        max_retries: Maximum number of retries after the first failure.
        backoff: Seconds to sleep between retries.
    """

    def _run() -> None:
        conn.commit()

    _retry_on_locked(_run, max_retries=max_retries, backoff=backoff)
