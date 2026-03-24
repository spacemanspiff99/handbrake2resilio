#!/usr/bin/env python3
"""Unit tests for shared.db SQLite helpers."""

import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

from shared.db import (  # noqa: E402
    commit_with_retry,
    execute_with_retry,
    get_db_connection,
)


class TestGetDbConnection(unittest.TestCase):
    """Tests for get_db_connection pragmas and connect options."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_wal_and_busy_timeout(self) -> None:
        with get_db_connection(self.db_path) as conn:
            row = conn.execute("PRAGMA journal_mode;").fetchone()
            self.assertEqual(row[0].lower(), "wal")
            busy = conn.execute("PRAGMA busy_timeout;").fetchone()
            self.assertEqual(busy[0], 30000)

    @patch("shared.db.sqlite3.connect")
    def test_connect_uses_check_same_thread_and_timeout(
        self, mock_connect: MagicMock
    ) -> None:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        get_db_connection("/tmp/x.db")

        mock_connect.assert_called_once()
        kwargs = mock_connect.call_args.kwargs
        self.assertFalse(kwargs["check_same_thread"])
        self.assertEqual(kwargs["timeout"], 30.0)


class TestExecuteWithRetry(unittest.TestCase):
    """Tests for execute_with_retry."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "retry.db")

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_succeeds_without_retry(self) -> None:
        with get_db_connection(self.db_path) as conn:
            execute_with_retry(conn, "CREATE TABLE t (id INTEGER PRIMARY KEY);")
            commit_with_retry(conn)
            cur = execute_with_retry(conn, "INSERT INTO t (id) VALUES (1);")
            self.assertIsNotNone(cur)

    @patch("shared.db.time.sleep", return_value=None)
    def test_retries_on_locked_then_succeeds(self, _sleep: MagicMock) -> None:
        conn = MagicMock()
        calls = {"n": 0}
        cursor = MagicMock()

        def flaky_execute(
            *_args: object, **_kwargs: object
        ) -> MagicMock:
            calls["n"] += 1
            if calls["n"] < 2:
                raise sqlite3.OperationalError("database is locked")
            return cursor

        conn.execute.side_effect = flaky_execute

        result = execute_with_retry(conn, "SELECT 1;")
        self.assertEqual(calls["n"], 2)
        self.assertIs(result, cursor)

    @patch("shared.db.time.sleep", return_value=None)
    def test_raises_after_max_retries(self, _sleep: MagicMock) -> None:
        conn = MagicMock()
        conn.execute.side_effect = sqlite3.OperationalError("database is locked")

        with self.assertRaises(sqlite3.OperationalError):
            execute_with_retry(conn, "SELECT 1;", max_retries=3, backoff=0.01)

        self.assertEqual(conn.execute.call_count, 4)

    def test_non_lock_operational_error_not_retried(self) -> None:
        conn = MagicMock()
        conn.execute.side_effect = sqlite3.OperationalError(
            "no such table: missing"
        )

        with self.assertRaises(sqlite3.OperationalError):
            execute_with_retry(conn, "SELECT * FROM missing;")

        conn.execute.assert_called_once()


if __name__ == "__main__":
    unittest.main()
