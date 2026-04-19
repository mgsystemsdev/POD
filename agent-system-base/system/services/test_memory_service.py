"""Tests for memory_service (upsert by key)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import contextmanager
from pathlib import Path

_SERVICES_DIR = Path(__file__).resolve().parent
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

import db as db_mod  # noqa: E402
import memory_service  # noqa: E402
import project_service  # noqa: E402

_real_connect = db_mod.connect


class TestMemoryService(unittest.TestCase):
    def setUp(self) -> None:
        fd, self._db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(self._db_path) and os.unlink(self._db_path))

        @contextmanager
        def _patched_connect(*, database: str | None = None, uri: bool = False):
            if database is None:
                with _real_connect(database=self._db_path) as conn:
                    yield conn
            else:
                with _real_connect(database=database, uri=uri) as conn:
                    yield conn

        self._patcher = unittest.mock.patch.object(memory_service.db, "connect", _patched_connect)
        self._patcher.start()
        self._patcher2 = unittest.mock.patch.object(project_service.db, "connect", _patched_connect)
        self._patcher2.start()
        self._pid = project_service.create_project("T", "t", root_path="/tmp").get("id")
        assert self._pid is not None

    def tearDown(self) -> None:
        self._patcher2.stop()
        self._patcher.stop()

    def test_upsert_same_key_single_row(self) -> None:
        pid = self._pid
        a = memory_service.upsert_memory(pid, "ctx", "first")
        b = memory_service.upsert_memory(pid, "ctx", "second")
        self.assertEqual(a["id"], b["id"])
        self.assertEqual(b["value"], "second")
        rows = memory_service.list_memory(project_id=pid)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["key"], "ctx")
        self.assertEqual(rows[0]["value"], "second")

    def test_get_memory(self) -> None:
        pid = self._pid
        memory_service.upsert_memory(pid, "k1", "v1")
        got = memory_service.get_memory(pid, "k1")
        assert got is not None
        self.assertEqual(got["value"], "v1")
        self.assertIsNone(memory_service.get_memory(pid, "missing"))

    def test_two_keys_two_rows(self) -> None:
        pid = self._pid
        memory_service.upsert_memory(pid, "a", "1")
        memory_service.upsert_memory(pid, "b", "2")
        self.assertEqual(len(memory_service.list_memory(project_id=pid)), 2)

    def test_empty_key_raises(self) -> None:
        with self.assertRaises(ValueError):
            memory_service.upsert_memory(self._pid, "  ", "x")


if __name__ == "__main__":
    unittest.main()
