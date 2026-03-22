"""Shared SQLite database helper with WAL mode and busy timeout."""

import sqlite3


def get_db_connection(db_path: str, timeout: int = 5000) -> sqlite3.Connection:
    """
    Open a SQLite connection with WAL journal mode and busy timeout.

    WAL mode allows concurrent readers with one writer, preventing
    'database is locked' errors when api-gateway and handbrake-service
    write simultaneously.

    Args:
        db_path: Path to the SQLite database file.
        timeout: Busy wait timeout in milliseconds (default 5000ms).

    Returns:
        sqlite3.Connection with WAL mode and busy timeout set.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(f"PRAGMA busy_timeout={timeout};")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn
