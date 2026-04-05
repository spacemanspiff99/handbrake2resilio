"""Unit tests for shared/db.py — SQLite connection helpers."""
from __future__ import annotations

import os
import sqlite3
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db import get_db_connection


class TestGetDbConnection:
    """Tests for get_db_connection context manager."""

    def test_returns_connection(self, tmp_path: pytest.TempPathFactory) -> None:
        """get_db_connection returns a valid sqlite3.Connection."""
        db_path = str(tmp_path / "test.db")
        conn = get_db_connection(db_path)
        try:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)
        finally:
            conn.close()

    def test_wal_mode_enabled(self, tmp_path: pytest.TempPathFactory) -> None:
        """Connection uses WAL journal mode for better concurrency."""
        db_path = str(tmp_path / "test.db")
        conn = get_db_connection(db_path)
        try:
            row = conn.execute("PRAGMA journal_mode").fetchone()
            assert row[0].lower() == "wal"
        finally:
            conn.close()

    def test_busy_timeout_set(self, tmp_path: pytest.TempPathFactory) -> None:
        """Connection has busy_timeout set (non-zero)."""
        db_path = str(tmp_path / "test.db")
        conn = get_db_connection(db_path)
        try:
            row = conn.execute("PRAGMA busy_timeout").fetchone()
            assert row[0] >= 1000  # at least 1 second
        finally:
            conn.close()

    def test_row_factory_set(self, tmp_path: pytest.TempPathFactory) -> None:
        """Connection row_factory is sqlite3.Row for dict-like access."""
        db_path = str(tmp_path / "test.db")
        conn = get_db_connection(db_path)
        try:
            assert conn.row_factory is sqlite3.Row
        finally:
            conn.close()

    def test_connection_is_usable(self, tmp_path: pytest.TempPathFactory) -> None:
        """Connection can execute basic SQL immediately after creation."""
        db_path = str(tmp_path / "test.db")
        conn = get_db_connection(db_path)
        try:
            result = conn.execute("SELECT 1").fetchone()
            assert result[0] == 1
        finally:
            conn.close()

    def test_concurrent_writes_no_deadlock(self, tmp_path: pytest.TempPathFactory) -> None:
        """Multiple threads can write to the same DB without deadlocking."""
        db_path = str(tmp_path / "concurrent.db")
        # Create table first
        conn = get_db_connection(db_path)
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, val TEXT)")
        conn.commit()
        conn.close()

        errors: list[Exception] = []

        def write_row(n: int) -> None:
            try:
                c = get_db_connection(db_path)
                c.execute("INSERT INTO items (val) VALUES (?)", (f"row{n}",))
                c.commit()
                c.close()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=write_row, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Concurrent write errors: {errors}"
